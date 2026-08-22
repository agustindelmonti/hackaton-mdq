"""
disponibilidad.py · «¿Tengo o no tengo?» — y si no tengo, de dónde lo saco.

ESTE ES EL MÓDULO QUE ABRE LA DEMO, Y SALE DE UNA FRASE TEXTUAL DEL DUEÑO:

    «Estoy yendo a un campo y me dicen: che, necesito 1.200 bolsas de Spunta,
     ¿tenés? Y digo: pará, tengo que anotarlo en el bloc de notas. […] Entonces
     es tener algo — no te digo en dos segundos, pero decir: hay tanta vendida,
     hay tantas guardadas, tengo o no tengo.»

Y del error que más les duele:

    «Piden que salgan papas de la planta para vender a un cliente y en realidad
     no hay stock. […] Estaría bueno que antes de que se lleve a cabo esa venta
     salte una alerta: che, no hay tanto en este lugar. Entonces no se puede
     efectuar esta venta en este lote. Se puede efectuar esa venta yendo a este
     otro lote, que sí tiene esa variedad de papas a disposición.»

Fijate lo que pidieron: **frenar Y resolver**. Un sistema que sólo frena es una
traba más. El que dice «no acá, pero sí allá, y son estos lotes» es una
herramienta.

---

EL STOCK NO ES UN CAMPO. SE DERIVA.

Nunca hay una celda que diga «acá hay 12.186 kg». El stock es el resultado de
recorrer el libro de movimientos y ver qué quedó. Por eso no se puede pisar, no
tiene conflicto de versiones, y todo número se puede abrir hasta el remito.

EL LIBRO DE PARTIDAS

Cada entrada a una ubicación abre una **partida**: tantos kilos de tal lote, con
tal calibre, en tal bolsa de tal color con tal hilo. Cada salida consume
partidas. Eso permite responder no sólo «cuánto hay» sino **«de qué remito salió
cada kilo»**, que es lo que pidieron cuando dijeron que querían verlo
desagregado, camión por camión.

Para decidir qué partida consume una salida, se usa el mismo criterio que usan
ellos en la cámara: **la tarjeta y los colores**. Un retiro que dice «bolsa
roja-hilo blanco» sale de la partida que entró con bolsa roja e hilo blanco. Si
no hay match por color, se cae a calibre, y al final a la más vieja primero.

EL SALDO ANTERIOR — el número honesto

La planilla 2026 empieza en febrero, pero la papa ya estaba. Cuando una salida
pide más kilos de los que el libro tiene, NO se inventa el faltante ni se deja
el saldo en negativo: se abre una partida de **saldo anterior** que dice
exactamente eso — «esto entró antes de que empezara esta planilla» — con el
movimiento que lo puso en evidencia. Es información vieja hecha visible, que es
todo el problema que vinieron a contarnos.

LA CLASIFICACIÓN

La papa llega a la planta a granel, en tolva, y ahí se clasifica: «la planta se
reclasifica y de ahí puede tener más destinos». Por eso lo que está en la planta
está mayormente **sin clasificar**, y lo que está en un frigorífico ya tiene
calibre: llegó clasificado. Tener 1.100.000 kg de Spunta sin clasificar no es
tener 1.100.000 kg de Spunta exportación, y el sistema no los confunde nunca.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from . import papasud_real as real
from .fechas import hoy
from .paths import DATA_DIR

# ---------------------------------------------------------------------------
# El orden de los calibres. Uno más alto sirve para un pedido más bajo — con
# pérdida de plata, y por eso se avisa. Al revés no: mandar granel donde piden
# exportación es el contenedor que vuelve.
# ---------------------------------------------------------------------------
ORDEN_CALIBRE = {
    "exportacion": 3,
    "sin chicas": 2,
    "recibo": 1,
    "granel": 1,
    "descarte de exportacion": 0,
    "descarte paraguay": 0,
    "sin clasificar": -1,           # está, pero todavía no se sabe qué es
}
SIN_CLASIFICAR = "sin clasificar"

# Un kilo por bolsa razonable cuando el lote todavía no tiene promedio propio.
# Es el promedio real de toda la planilla, no un número redondo elegido a dedo.
KG_BOLSA_FALLBACK = 50.0


def _nivel(calibre: str | None) -> int:
    return ORDEN_CALIBRE.get(calibre or SIN_CLASIFICAR, 0)


# ===========================================================================
# EL LIBRO — recorrer los movimientos y ver qué quedó
# ===========================================================================
@lru_cache(maxsize=1)
def libro() -> dict:
    partidas: list[dict] = []
    por_ubic_lote: dict[tuple[str, str], list[dict]] = {}
    saldos: list[dict] = []
    n = 0

    def abrir(mov: dict, ubic: str, kg: float, *, anterior=False, motivo=None) -> dict:
        nonlocal n
        n += 1
        p = {
            "id": f"PAR-{n:06d}",
            "ubicacion": ubic,
            "lote": mov.get("lote"),
            "variedad": mov.get("variedad"),
            "calibre": mov.get("calibre") or SIN_CLASIFICAR,
            "categoria": mov.get("categoria"),
            "bolsa_color": mov.get("bolsa_color"),
            "hilo_color": mov.get("hilo_color"),
            "kg_inicial": round(kg),
            "kg": round(kg),
            "kg_prom": mov.get("kg_prom"),
            "granel": bool(mov.get("granel")),
            "anomalias": list(mov.get("anomalias") or []),
            "fecha": mov.get("fecha"),
            "remito": mov.get("remito"),
            "dtv": mov.get("dtv"),
            "movimiento": mov["id"],
            "tipo_ingreso": mov.get("tipo"),
            "desde": real.nombre_nodo(mov.get("origen")),
            "fuente": mov.get("fuente"),
            "saldo_anterior": anterior,
            "motivo_saldo": motivo,
            "consumos": [],
        }
        partidas.append(p)
        por_ubic_lote.setdefault((ubic, p["lote"] or ""), []).append(p)
        return p

    def consumir(mov: dict, ubic: str, kg: float) -> list[dict]:
        """Saca `kg` de la ubicación. Devuelve de qué partidas salieron.

        El orden de preferencia es el de la cámara real: primero la partida que
        coincide en colores —que es la tarjeta que el operario está mirando—,
        después la que coincide en calibre, y al final la más vieja.
        """
        disponibles = [p for p in por_ubic_lote.get((ubic, mov.get("lote") or ""), [])
                       if p["kg"] > 0]
        cal, bc, hc = mov.get("calibre"), mov.get("bolsa_color"), mov.get("hilo_color")

        def prioridad(p: dict) -> tuple:
            color_ok = bc and p["bolsa_color"] == bc and (not hc or p["hilo_color"] == hc)
            cal_ok = cal and p["calibre"] == cal
            return (0 if color_ok else 1, 0 if cal_ok else 1, p["fecha"] or "")

        disponibles.sort(key=prioridad)
        falta = kg
        salidas: list[dict] = []
        for p in disponibles:
            if falta <= 0.5:
                break
            toma = min(p["kg"], falta)
            p["kg"] = round(p["kg"] - toma)
            p["consumos"].append({"movimiento": mov["id"], "remito": mov.get("remito"),
                                  "fecha": mov.get("fecha"), "kg": round(toma),
                                  "hacia": real.nombre_nodo(mov.get("destino"))})
            salidas.append({"partida": p["id"], "kg": round(toma),
                            "remito_origen": p["remito"], "calibre": p["calibre"]})
            falta -= toma

        if falta > 0.5:
            # El libro no alcanza. No se inventa el faltante ni se deja negativo:
            # se declara que esa papa entró antes de que empezara esta planilla.
            motivo = (f"el movimiento {mov['id']} del "
                      f"{_dia(mov.get('fecha'))} sacó {_num(kg)} kg de "
                      f"{real.nombre_ubicacion(ubic)} y esta planilla no registra "
                      f"cuándo entraron")
            p = abrir(mov, ubic, falta, anterior=True, motivo=motivo)
            p["fecha"] = None
            p["remito"] = None
            p["kg"] = 0
            p["consumos"].append({"movimiento": mov["id"], "remito": mov.get("remito"),
                                  "fecha": mov.get("fecha"), "kg": round(falta),
                                  "hacia": real.nombre_nodo(mov.get("destino"))})
            saldos.append({
                "ubicacion": ubic, "lote": mov.get("lote"),
                "variedad": mov.get("variedad"), "kg": round(falta),
                "motivo": motivo, "movimiento": mov["id"],
                "fuente": mov.get("fuente"),
            })
            salidas.append({"partida": p["id"], "kg": round(falta),
                            "remito_origen": None, "calibre": p["calibre"],
                            "saldo_anterior": True})
        return salidas

    for mov in real.movimientos():
        kg = mov.get("kg") or 0
        if not kg:
            continue
        o, d = mov.get("origen"), mov.get("destino")
        # 'saco p/trabajar en cecive': sale y vuelve al mismo lugar. No mueve stock.
        if mov.get("reingresa") or (real.es_nodo_de_stock(o) and o == d):
            continue
        if real.es_nodo_de_stock(o):
            mov["_salidas"] = consumir(mov, o["id"], kg)
        if real.es_nodo_de_stock(d):
            abrir(mov, d["id"], kg)

    return {
        "partidas": partidas,
        "saldos_anteriores": saldos,
        "saldo_anterior_kg": round(sum(s["kg"] for s in saldos)),
    }


def refrescar() -> None:
    libro.cache_clear()
    _kg_prom_lote.cache_clear()
    real.refrescar()


# ---------------------------------------------------------------------------
# Formato — un dueño en el auto no lee un float
# ---------------------------------------------------------------------------
def _num(v) -> str:
    return f"{round(v or 0):,}".replace(",", ".")


def _dia(iso: str | None) -> str:
    if not iso:
        return "sin fecha"
    a, m, d = iso.split("-")
    return f"{d}/{m}"


# ---------------------------------------------------------------------------
# Bolsas ↔ kilos. NO hay constante: cada lote tiene su promedio real.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _kg_prom_lote() -> dict[str, float]:
    return {l["id"]: l["kg_prom"] for l in real.lotes() if l.get("kg_prom")}


def kg_por_bolsa(*, lote: str | None = None, variedad: str | None = None) -> tuple[float, str]:
    """Devuelve el kilo por bolsa y de dónde salió, para poder mostrarlo."""
    if lote and lote in _kg_prom_lote():
        return _kg_prom_lote()[lote], f"promedio real del lote {lote}"
    if variedad:
        ls = [l for l in real.lotes() if l.get("variedad") == variedad and l.get("kg_prom")]
        if ls:
            v = sum(l["kg_prom"] for l in ls) / len(ls)
            return round(v, 2), f"promedio de los {len(ls)} lotes de {variedad}"
    return KG_BOLSA_FALLBACK, "promedio general de la planilla"


def a_kg(cantidad: float, unidad: str, *, lote=None, variedad=None) -> tuple[float, str]:
    if unidad != "bolsas":
        return cantidad, ""
    kb, fuente = kg_por_bolsa(lote=lote, variedad=variedad)
    return cantidad * kb, f"{_num(cantidad)} bolsas a {kb:.2f} kg ({fuente})"


def a_bolsas(kg: float, *, lote=None, variedad=None) -> int:
    kb, _ = kg_por_bolsa(lote=lote, variedad=variedad)
    return int(kg // kb)


def _bolsas_de(p: dict) -> int:
    """Lo que entró a granel —en tolva, suelto y con tierra— no está en bolsas.
    Contarlo como bolsas es el error que un encargado ve en dos segundos."""
    if p.get("granel"):
        return 0
    return a_bolsas(p["kg"], lote=p["lote"], variedad=p["variedad"])


# ===========================================================================
# CONSULTA DE STOCK
# ===========================================================================
def partidas(*, variedad=None, calibre=None, ubicacion=None, lote=None,
             calibre_minimo=False, con_saldo_cero=False) -> list[dict]:
    ps = libro()["partidas"]
    out = []
    for p in ps:
        if not con_saldo_cero and p["kg"] <= 0:
            continue
        if variedad and p["variedad"] != variedad:
            continue
        if ubicacion and p["ubicacion"] != ubicacion:
            continue
        if lote and p["lote"] != lote:
            continue
        if calibre:
            if calibre_minimo:
                if _nivel(p["calibre"]) < _nivel(calibre):
                    continue
            elif p["calibre"] != calibre:
                continue
        out.append(p)
    return out


def resumen(ps: list[dict]) -> dict:
    """Los mismos kilos, mirados por ubicación, por lote y por calibre.

    Cada corte lista los remitos que lo sostienen: el número se abre y se ve.
    """
    def agrupar(clave):
        g: dict = {}
        for p in ps:
            k = clave(p)
            d = g.setdefault(k, {"clave": k, "kg": 0, "bolsas": 0, "kg_granel": 0,
                                 "partidas": 0, "remitos": [], "anomalias": [],
                                 "saldo_anterior_kg": 0})
            d["kg"] += p["kg"]
            d["partidas"] += 1
            d["bolsas"] += _bolsas_de(p)
            d["kg_granel"] = d.get("kg_granel", 0) + (p["kg"] if p.get("granel") else 0)
            for a in p.get("anomalias") or []:
                if a not in d.setdefault("anomalias", []):
                    d["anomalias"].append(a)
            if p["saldo_anterior"]:
                d["saldo_anterior_kg"] += p["kg"]
            elif p["remito"] and p["remito"] not in d["remitos"]:
                d["remitos"].append(p["remito"])
        return sorted(g.values(), key=lambda d: -d["kg"])

    kg = sum(p["kg"] for p in ps)
    return {
        "kg": round(kg),
        "bolsas": sum(_bolsas_de(p) for p in ps),
        "kg_granel": round(sum(p["kg"] for p in ps if p.get("granel"))),
        "partidas": len(ps),
        "saldo_anterior_kg": round(sum(p["kg"] for p in ps if p["saldo_anterior"])),
        "por_ubicacion": agrupar(lambda p: p["ubicacion"]),
        "por_lote": agrupar(lambda p: p["lote"]),
        "por_calibre": agrupar(lambda p: p["calibre"]),
        "por_variedad": agrupar(lambda p: p["variedad"]),
    }


# ===========================================================================
# COMPROMISOS — tener no es lo mismo que poder vender
# ===========================================================================
PEDIDOS_JSON = os.path.join(DATA_DIR, "pedidos.json")
PEDIDOS_SEED = os.path.join(DATA_DIR, "pedidos_abiertos.seed.json")


def _pedidos_todos() -> list[dict]:
    ruta = PEDIDOS_JSON if os.path.isfile(PEDIDOS_JSON) else PEDIDOS_SEED
    if not os.path.isfile(ruta):
        return []
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def _guardar_pedidos(ps: list[dict]) -> None:
    with open(PEDIDOS_JSON, "w", encoding="utf-8") as fh:
        json.dump(ps, fh, ensure_ascii=False, indent=1)


def pedidos_abiertos(*, variedad=None, ubicacion=None, calibre=None,
                     lote=None) -> list[dict]:
    out = []
    for p in _pedidos_todos():
        if p.get("estado") != "abierto":
            continue
        if variedad and p.get("variedad") != variedad:
            continue
        if ubicacion and p.get("ubicacion") != ubicacion:
            continue
        if calibre and p.get("calibre") != calibre:
            continue
        # Un pedido sólo compromete a un lote si tiene ESE lote asignado. Los
        # que todavía no eligieron lote no se le cuelgan a ninguno: se avisan
        # aparte, que es distinto de darlos por reservados en el lote de al lado.
        if lote and lote not in (p.get("lotes") or []):
            continue
        out.append(p)
    return sorted(out, key=lambda p: p.get("entrega") or "")


def _kg_pedido(p: dict) -> float:
    if p.get("kg"):
        return float(p["kg"])
    kb, _ = kg_por_bolsa(variedad=p.get("variedad"))
    return float(p.get("bolsas") or 0) * kb


def comprometido(*, variedad=None, ubicacion=None, calibre=None, lote=None) -> dict:
    ps = pedidos_abiertos(variedad=variedad, ubicacion=ubicacion,
                          calibre=calibre, lote=lote)
    d = {"kg": round(sum(_kg_pedido(p) for p in ps)), "pedidos": ps}
    if lote:
        sueltos = [p for p in pedidos_abiertos(variedad=variedad, ubicacion=ubicacion,
                                               calibre=calibre)
                   if not p.get("lotes")]
        d["sin_lote_asignado"] = {"kg": round(sum(_kg_pedido(p) for p in sueltos)),
                                  "pedidos": sueltos}
    return d


# ===========================================================================
# LA RESPUESTA — corta primero, el detalle si lo piden
# ===========================================================================
def consultar(*, variedad=None, calibre=None, ubicacion=None, lote=None,
              cantidad=None, unidad="kg") -> dict:
    """«¿Tengo 1.200 bolsas de Spunta?» · «¿Qué hay en dospanca?»

    Devuelve las cinco capas que pidieron, en este orden:
      1. sí o no, y cuánto hay          4. de qué lotes, categoría y calibre
      2. dónde está                     5. los remitos que lo respaldan
      3. cuánto comprometido, cuánto libre
    """
    if lote and not variedad:
        variedad = (real.lote_por_id().get(lote) or {}).get("variedad")
    ps = partidas(variedad=variedad, calibre=calibre, ubicacion=ubicacion, lote=lote)
    r = resumen(ps)
    comp = comprometido(variedad=variedad, ubicacion=ubicacion, calibre=calibre,
                        lote=lote)
    libre_kg = max(0, r["kg"] - comp["kg"])

    pedido_kg = conversion = None
    alcanza = None
    if cantidad:
        pedido_kg, conversion = a_kg(float(cantidad), unidad, lote=lote, variedad=variedad)
        alcanza = libre_kg >= pedido_kg

    return {
        "pregunta": {"variedad": variedad, "calibre": calibre, "ubicacion": ubicacion,
                     "lote": lote, "cantidad": cantidad, "unidad": unidad},
        "hay": r["kg"],
        "hay_bolsas": r["bolsas"],
        "comprometido": comp["kg"],
        "libre": libre_kg,
        "libre_bolsas": a_bolsas(libre_kg - r.get("kg_granel", 0), lote=lote,
                                 variedad=variedad) if libre_kg > r.get("kg_granel", 0) else 0,
        "alcanza": alcanza,
        "pedido_kg": None if pedido_kg is None else round(pedido_kg),
        "conversion": conversion,
        "falta_kg": None if pedido_kg is None else max(0, round(pedido_kg - libre_kg)),
        "resumen": r,
        "pedidos_abiertos": comp["pedidos"],
        "titular": _titular(r, comp, libre_kg, pedido_kg, alcanza, variedad, calibre,
                            ubicacion, unidad, cantidad, lote),
        "advertencias": _advertencias(r, ps),
    }


def _titular(r, comp, libre, pedido_kg, alcanza, variedad, calibre, ubicacion,
             unidad, cantidad, lote=None) -> str:
    """Una línea. El dueño está manejando: no lee una tabla."""
    if lote:
        que = f"el lote {lote}" + (f" ({variedad})" if variedad else "")
    else:
        que = variedad.title() if variedad else "stock"
    if calibre:
        que += f" {calibre}"
    donde = f" en {real.nombre_ubicacion(ubicacion)}" if ubicacion else ""
    if pedido_kg is None:
        if not r["kg"]:
            return f"No hay {que}{donde}."
        s = (f"{que[0].upper()}{que[1:]}{donde} tiene {_num(r['kg'])} kg" if lote
             else f"Hay {_num(r['kg'])} kg de {que}{donde}")
        if r["bolsas"]:
            s += f" ({_num(r['bolsas'])} bolsas)"
        if comp["kg"]:
            s += f". Comprometidos {_num(comp['kg'])} kg — libres {_num(libre)}"
        return s + "."
    cant = f"{_num(cantidad)} {unidad}" if unidad == "bolsas" else None
    sufijo = f" ({cant})" if cant else ""
    if alcanza:
        return (f"Sí. Tenés {_num(libre)} kg libres de {que}{donde} "
                f"y el pedido son {_num(pedido_kg)} kg{sufijo}.")
    return (f"No alcanza. Piden {_num(pedido_kg)} kg{sufijo} de {que}{donde} "
            f"y hay {_num(libre)} kg libres: faltan {_num(pedido_kg - libre)} kg.")


def _advertencias(r: dict, ps: list[dict]) -> list[dict]:
    av = []
    if r["saldo_anterior_kg"]:
        av.append({
            "id": "saldo_anterior",
            "texto": f"{_num(r['saldo_anterior_kg'])} kg de estos vienen de antes de "
                     f"febrero 2026: la planilla no registra cuándo entraron.",
        })
    sc = sum(p["kg"] for p in ps if p["calibre"] == SIN_CLASIFICAR)
    if sc:
        av.append({
            "id": "sin_clasificar",
            "texto": f"{_num(sc)} kg están sin clasificar — llegaron a granel y "
                     f"todavía no pasaron por la clasificadora.",
        })
    # La planilla registra mejor lo que entra que lo que sale: es más fácil
    # anotar el camión que llega que el que se va. Cuando el libro deja una
    # ubicación muy cargada, lo decimos en vez de mostrar el número a secas.
    en_planta = sum(p["kg"] for p in ps if p["ubicacion"] == "planta_mdp")
    if en_planta and r["kg"] and en_planta / r["kg"] > 0.5 and en_planta > 100_000:
        av.append({
            "id": "concentrado_en_planta",
            "texto": f"{_num(en_planta)} kg —el {en_planta / r['kg'] * 100:.0f}%— "
                     f"figuran en la planta. Es lo que el libro dice que entró y "
                     f"no registra que haya salido: si no coincide con lo que ves, "
                     f"faltan cargar salidas.",
        })
    anom = {a for p in ps for a in (p.get("anomalias") or [])}
    if anom:
        av.append({
            "id": "filas_marcadas",
            "texto": "Parte de estos kilos vienen de filas de la planilla que "
                     "quedaron marcadas: " + ", ".join(sorted(anom)) + ".",
            "anomalias": sorted(anom),
        })
    return av


# ===========================================================================
# EL BLOQUEO CON ALTERNATIVA — frenar y resolver
# ===========================================================================
DIAS_RETIRO_FRIO = 3          # lo que tarda mandar un camión a buscar a la cámara


def evaluar_pedido(*, variedad: str, cantidad: float, unidad: str = "kg",
                   calibre: str | None = None, ubicacion: str | None = None,
                   cliente: str | None = None) -> dict:
    """Antes de comprometer stock: ¿se puede? Y si no, ¿cómo sí?

    Esto es lo que pidieron textual: que salte la alerta ANTES de que la venta
    se efectúe, diciendo que en ese lugar no hay — y que se puede hacer yendo a
    este otro lote, que sí tiene esa variedad a disposición.
    """
    pedido_kg, conversion = a_kg(float(cantidad), unidad, variedad=variedad)
    calibre = calibre or None

    aqui = consultar(variedad=variedad, calibre=calibre, ubicacion=ubicacion)
    if aqui["libre"] >= pedido_kg:
        return {
            "resultado": "se_puede",
            "pedido": _pedido_dict(variedad, cantidad, unidad, calibre, ubicacion,
                                   cliente, pedido_kg, conversion),
            "titular": (f"Se puede. {_num(aqui['libre'])} kg libres de "
                        f"{variedad.title()}{' ' + calibre if calibre else ''}"
                        f"{' en ' + real.nombre_ubicacion(ubicacion) if ubicacion else ''}"
                        f" contra {_num(pedido_kg)} kg del pedido."),
            "aqui": aqui,
            "origenes": _armar_origenes(
                partidas(variedad=variedad, calibre=calibre, ubicacion=ubicacion,
                         calibre_minimo=bool(calibre)), pedido_kg),
            "alternativas": [],
        }

    falta = pedido_kg - aqui["libre"]
    return {
        "resultado": "bloqueado",
        "pedido": _pedido_dict(variedad, cantidad, unidad, calibre, ubicacion,
                               cliente, pedido_kg, conversion),
        "titular": _titular_bloqueo(aqui, variedad, calibre, ubicacion, pedido_kg, falta),
        "motivo": _motivo(aqui, ubicacion, falta),
        "aqui": aqui,
        "falta_kg": round(falta),
        "alternativas": _alternativas(variedad, calibre, ubicacion, falta),
    }


def _pedido_dict(variedad, cantidad, unidad, calibre, ubicacion, cliente,
                 pedido_kg, conversion) -> dict:
    return {
        "variedad": variedad, "cantidad": cantidad, "unidad": unidad,
        "calibre": calibre, "ubicacion": ubicacion, "cliente": cliente,
        "kg": round(pedido_kg), "conversion": conversion,
    }


def _titular_bloqueo(aqui, variedad, calibre, ubicacion, pedido_kg, falta) -> str:
    donde = f" en {real.nombre_ubicacion(ubicacion)}" if ubicacion else ""
    que = f"{variedad.title()}{' ' + calibre if calibre else ''}"
    return (f"No se puede: faltan {_num(falta)} kg. "
            f"El pedido son {_num(pedido_kg)} kg de {que}{donde} y hay "
            f"{_num(aqui['libre'])} kg libres.")


def _motivo(aqui: dict, ubicacion: str | None, falta: float) -> dict:
    """Por qué no alcanza: no es lo mismo que no haya a que esté vendido."""
    if aqui["hay"] and aqui["comprometido"]:
        pes = aqui["pedidos_abiertos"]
        detalle = "; ".join(
            f"{_num(_kg_pedido(p))} kg para {p.get('cliente', '').title()} el {_dia(p.get('entrega'))}"
            for p in pes[:3])
        return {
            "id": "comprometido",
            "texto": f"Hay {_num(aqui['hay'])} kg, pero {_num(aqui['comprometido'])} "
                     f"ya están comprometidos: {detalle}.",
            "pedidos": pes,
        }
    if aqui["hay"]:
        return {"id": "no_alcanza",
                "texto": f"Hay {_num(aqui['hay'])} kg y no alcanzan para el pedido."}
    donde = real.nombre_ubicacion(ubicacion) if ubicacion else "ninguna ubicación"
    return {"id": "no_hay", "texto": f"No hay nada de eso en {donde}."}


def _alternativas(variedad: str, calibre: str | None, ubicacion: str | None,
                  falta: float) -> list[dict]:
    """De dónde sale lo que falta. Ordenado por lo que menos cuesta mover.

    Cuatro cosas que una lista de stock no hace y ésta sí:
      · **no repite lo que ya contó** — si la pregunta no pidió una ubicación,
        el stock listo ya está contado y ofrecerlo de nuevo sería sumar dos
        veces la misma papa. Ése es el número inventado que nos hunde;
      · **verifica compatibilidad** — no ofrece granel para un pedido de
        exportación, porque eso es el contenedor que vuelve de destino;
      · **dice cuánto tarda y qué hay que hacer** — traer de un frigorífico es
        un camión y tres días; clasificar es pasarlo por la máquina;
      · **combina** — si con un lugar no alcanza, propone los dos.
    """
    alts: list[dict] = []

    # (a) Lo que YA está en condiciones, en otro lugar. Sólo tiene sentido si la
    #     pregunta fijó una ubicación: si no, ese stock ya entró en la cuenta.
    if ubicacion:
        listo = partidas(variedad=variedad, calibre=calibre,
                         calibre_minimo=bool(calibre))
        por_ubic: dict[str, list[dict]] = {}
        for p in listo:
            if p["ubicacion"] == ubicacion:
                continue                   # es donde falta, ya lo contamos
            por_ubic.setdefault(p["ubicacion"], []).append(p)
        for uid, lista in por_ubic.items():
            alt = _alt_ubicacion(uid, lista, variedad, calibre, falta)
            if alt:
                alts.append(alt)

    # (b) Lo que serviría pero necesita un paso previo. Acá vive la respuesta
    #     que cambia la conversación: hay mil toneladas de esa variedad en la
    #     planta, sin clasificar. No es lo mismo que tenerla lista — y decirlo
    #     con el número del muestreo atrás es lo que hace que se confíe.
    if calibre:
        crudo = [p for p in partidas(variedad=variedad)
                 if p["calibre"] == SIN_CLASIFICAR]
        por_ubic = {}
        for p in crudo:
            por_ubic.setdefault(p["ubicacion"], []).append(p)
        for uid, lista in por_ubic.items():
            alt = _alt_ubicacion(uid, lista, variedad, None, falta,
                                 preparacion="clasificar")
            if alt:
                alt["compatibilidad"] = _compatibilidad(lista, calibre, variedad)
                alts.append(alt)

    # Primero lo que está listo y en casa; después lo que hay que ir a buscar o
    # preparar. El orden es el costo real de conseguirlo, no el tamaño del número.
    alts.sort(key=lambda a: (0 if a["listo"] else 1, a["dias"], -a["cubre_kg"]))
    _marcar_combinacion(alts, falta)
    return alts


def _alt_ubicacion(uid: str, lista: list[dict], variedad: str,
                   calibre: str | None, falta: float,
                   preparacion: str | None = None) -> dict | None:
    kg = sum(p["kg"] for p in lista)
    comp = comprometido(variedad=variedad, ubicacion=uid, calibre=calibre)["kg"]
    libre = max(0, kg - comp)
    if libre <= 0:
        return None
    u = real.ubicacion_por_id().get(uid, {})
    es_frio = u.get("tipo") == "frigorifico"

    if preparacion == "clasificar":
        # Sin clasificar no se compromete como calibre: lo que sale de la
        # clasificadora lo dice la máquina, no la pantalla.
        que_hacer = ("hay que clasificarlo — llegó a granel y todavía no pasó "
                     "por la clasificadora")
        dias = 1 if not es_frio else DIAS_RETIRO_FRIO + 1
    elif es_frio:
        que_hacer = "retiro de frío — hay que mandar un camión a buscarlo"
        dias = DIAS_RETIRO_FRIO
    else:
        que_hacer = "está en casa, se carga directo"
        dias = 0

    return {
        "ubicacion": uid,
        "nombre": real.nombre_ubicacion(uid),
        "tipo": u.get("tipo"),
        "kg": round(kg), "comprometido": comp, "libre": round(libre),
        "bolsas": sum(_bolsas_de(p) for p in lista),
        "kg_granel": round(sum(p["kg"] for p in lista if p.get("granel"))),
        "listo": preparacion is None,
        "preparacion": preparacion,
        "alcanza_solo": libre >= falta,
        "cubre_kg": round(min(libre, falta)),
        "movimiento": que_hacer,
        "dias": dias,
        "propia": bool(u.get("propia")),
        "lotes": _armar_origenes(lista, min(libre, falta)),
        "compatibilidad": _compatibilidad(lista, calibre, variedad),
    }


def _armar_origenes(ps: list[dict], objetivo: float) -> list[dict]:
    """De qué lotes sale, y con qué remito atrás. Se sirve del más grande."""
    por_lote: dict[str, dict] = {}
    for p in ps:
        d = por_lote.setdefault(p["lote"], {
            "lote": p["lote"], "variedad": p["variedad"], "kg": 0, "bolsas": 0,
            "calibres": [], "categoria": p.get("categoria"), "remitos": [],
            "ubicaciones": [], "saldo_anterior_kg": 0, "fuentes": [],
        })
        d["kg"] += p["kg"]
        if p["calibre"] not in d["calibres"]:
            d["calibres"].append(p["calibre"])
        if p["ubicacion"] not in d["ubicaciones"]:
            d["ubicaciones"].append(p["ubicacion"])
        if p["saldo_anterior"]:
            d["saldo_anterior_kg"] += p["kg"]
        elif p["remito"]:
            if p["remito"] not in d["remitos"]:
                d["remitos"].append(p["remito"])
            if p.get("fuente") and len(d["fuentes"]) < 6:
                d["fuentes"].append({"remito": p["remito"], "fecha": p["fecha"],
                                     "kg": p["kg"], **p["fuente"]})
    out = sorted(por_lote.values(), key=lambda d: -d["kg"])
    resto = objetivo
    for d in out:
        d["bolsas"] = a_bolsas(d["kg"], lote=d["lote"])
        d["toma_kg"] = round(max(0, min(d["kg"], resto)))
        d["toma_bolsas"] = a_bolsas(d["toma_kg"], lote=d["lote"])
        lo = real.lote_por_id().get(d["lote"] or "", {})
        d["campo"] = lo.get("campo")
        d["pivote"] = lo.get("pivote")
        resto -= d["toma_kg"]
    return out


def _compatibilidad(ps: list[dict], calibre: str | None, variedad: str) -> dict:
    """¿Esto SIRVE para el pedido? No alcanza con que sea la misma variedad."""
    niveles = {p["calibre"] for p in ps}
    sin_clasificar = sum(p["kg"] for p in ps if p["calibre"] == SIN_CLASIFICAR)
    notas: list[str] = []
    apto = True

    if calibre:
        mejores = [c for c in niveles if c != calibre and _nivel(c) > _nivel(calibre)]
        if mejores:
            notas.append(f"parte es {', '.join(mejores)} — sirve para un pedido "
                         f"de {calibre}, pero se está entregando de más")
        if sin_clasificar:
            apto = False
            notas.append(f"{_num(sin_clasificar)} kg están sin clasificar: "
                         f"hay que pasarlos por la clasificadora antes de "
                         f"poder comprometerlos como {calibre}")
    m = real.muestra_de_variedad().get(variedad)
    if sin_clasificar and calibre:
        clave = {"exportacion": "exportacion", "sin chicas": "sin_chicas"}.get(calibre)
        pct = (m.get("reparto") or {}).get(clave) if m else None
        if pct:
            notas.append(
                f"el muestreo de pre-cosecha del lote {m['lote']} da {pct * 100:.1f}% "
                f"{calibre} — de esos {_num(sin_clasificar)} kg saldrían unos "
                f"{_num(sin_clasificar * pct)} kg")
        else:
            # Decir que no se sabe vale más que estimar con un porcentaje
            # prestado de otra variedad. El productor conoce su rinde.
            notas.append(f"no hay muestreo de pre-cosecha de {variedad} cargado: "
                         f"no se puede estimar cuánto de eso sale {calibre}")
    return {"apto": apto, "calibres": sorted(niveles), "notas": notas,
            "sin_clasificar_kg": round(sin_clasificar)}


def _marcar_combinacion(alts: list[dict], falta: float) -> None:
    """Si con una sola ubicación no alcanza, decir con cuáles sí."""
    if not alts or alts[0]["alcanza_solo"]:
        return
    acum, usadas = 0.0, []
    for a in alts:
        if acum >= falta:
            break
        acum += a["libre"]
        usadas.append(a)
    if acum >= falta and len(usadas) > 1:
        for a in usadas:
            a["en_combinacion"] = True
        usadas[0]["combinacion"] = {
            "ubicaciones": [a["nombre"] for a in usadas],
            "kg": round(acum),
            "texto": ("con un solo lugar no alcanza; sumando "
                      + " y ".join(a["nombre"] for a in usadas)
                      + f" se cubren los {_num(falta)} kg"),
        }


# ===========================================================================
# COMPROMETER — accionar desde la misma pantalla
# ===========================================================================
def comprometer(*, variedad: str, cantidad: float, unidad: str, cliente: str,
                calibre: str | None = None, ubicacion: str | None = None,
                entrega: str | None = None, lotes: list[str] | None = None,
                quien: str = "") -> dict:
    """Reserva stock para un pedido. Pasa por la MISMA evaluación que la
    pantalla: no hay puerta de atrás por la que salga un pedido sin verificar."""
    ev = evaluar_pedido(variedad=variedad, cantidad=cantidad, unidad=unidad,
                        calibre=calibre, ubicacion=ubicacion, cliente=cliente)
    if ev["resultado"] != "se_puede":
        return {"ok": False, "evaluacion": ev}

    ps = _pedidos_todos()
    nid = f"PED-{hoy().isoformat().replace('-', '')}-{len(ps) + 1:03d}"
    ps.append({
        "id": nid, "estado": "abierto", "cliente": cliente,
        "variedad": variedad, "calibre": calibre, "ubicacion": ubicacion,
        "kg": round(ev["pedido"]["kg"]),
        "bolsas": int(cantidad) if unidad == "bolsas" else None,
        "entrega": entrega, "creado": hoy().isoformat(), "creado_por": quien,
        "lotes": lotes or [o["lote"] for o in ev["origenes"] if o["toma_kg"]],
    })
    _guardar_pedidos(ps)
    return {"ok": True, "pedido": ps[-1], "evaluacion": ev}
