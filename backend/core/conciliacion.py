"""
conciliacion.py · N02 — lo declarado contra lo contado, y POR QUÉ no coinciden.

El brief pide dos cosas distintas y esta es la segunda:

    «Cuando hay una diferencia entre lo declarado y lo contado, el sistema no
    solo la señala — propone una hipótesis en lenguaje simple sobre cuál puede
    ser la causa más probable (por ejemplo: "un movimiento del 12/08
    posiblemente no se registró en destino").»

CÓMO SE CONSTRUYE ESA HIPÓTESIS — Y POR QUÉ NO LA INVENTA EL MODELO

Sería fácil pasarle la diferencia a un LLM y pedirle que especule. Suena bien y
no sirve: en una empresa que audita cada lote, una causa inventada es peor que
ningún dato. Acá la hipótesis se BUSCA en los datos, con reglas explícitas, y
cada una viaja con la evidencia que la sostiene — número de movimiento, fecha,
quién lo registró, qué nota lo menciona. Ángela después la cuenta en castellano,
pero no la inventa: la lee.

LAS REGLAS, EN ORDEN DE FUERZA (la primera que matchea gana):

  1. TRASLADO SIN CONFIRMAR EN DESTINO — hay un movimiento `en_transito` de ese
     lote, saliendo de esa ubicación, cuyos kilos explican el faltante. Es la
     causa más frecuente y la más barata de arreglar: alguien tiene que ir a
     mirar si los bolsones están en el otro depósito.
  2. CANTIDAD MAL TIPEADA — un movimiento reciente del lote cuya cantidad, leída
     con un cero de más o de menos, cierra la diferencia exacta. El clásico de
     la planilla: 42.000 donde eran 4.200.
  3. MERMA FÍSICA CON TESTIGO — la diferencia es negativa y hay una nota del
     equipo o una condición de la cámara (temperatura fuera de rango, brotación)
     que la explica. La evidencia es la nota, con su autor y su fecha.
  4. TARA DE BOLSÓN — la diferencia es menor al umbral que el encargado le
     enseñó al sistema. No es un faltante: un bolsón nunca pesa mil justo. Esta
     no genera alerta; se registra como explicada y se calla.
  5. SIN CAUSA EN LOS DATOS — no hay nada que la explique. El sistema lo dice
     así, con todas las letras, y propone el conteo de control. Es la respuesta
     honesta y también la más útil: dice dónde hay que ir a mirar.
"""
from __future__ import annotations

from . import conocimiento, esquema, movimientos, notas, semilla, store
from .fechas import hoy, parse_fecha

APARTADO = "conteos"

# Por debajo de esto una diferencia es tara, no faltante. El default sale del
# oficio; si el encargado le enseñó otro número al sistema (core/conocimiento),
# manda el suyo.
UMBRAL_TARA_PCT_DEFAULT = 0.5

# Para la regla del cero de más: cuán cerca tiene que quedar la cuenta para que
# valga como explicación (en kilos, sobre una diferencia de miles).
TOLERANCIA_MATCH_KG = 60.0


def _conteos() -> list[dict]:
    return esquema.filas(APARTADO)


def hay_datos() -> bool:
    return bool(_conteos())


def _umbral_tara_pct() -> tuple[float, dict | None]:
    """El umbral vigente y la pieza de conocimiento que lo fijó (si hay una)."""
    reglas = [p for p in conocimiento.aplicables(nodo="deposito", efecto="suprime_alerta")
              if (p.get("params") or {}).get("umbral_pct") is not None]
    if reglas:
        r = reglas[0]
        return float(r["params"]["umbral_pct"]), r
    return UMBRAL_TARA_PCT_DEFAULT, None


# ---------------------------------------------------------------------------
# Las diferencias
# ---------------------------------------------------------------------------
def diferencias(incluir_explicadas: bool = True) -> list[dict]:
    """Cada conteo con su diferencia contra lo declarado y su hipótesis.

    Ordenadas por kilos en juego: la de arriba es la que más plata mueve, no la
    más vieja."""
    umbral_pct, regla = _umbral_tara_pct()
    arts = {a.get("codigo"): a for a in store.raw_actual()}
    out = []
    for c in _conteos():
        dif = float(c.get("diferencia_kg") or 0)
        if dif == 0:
            continue
        declarado = float(c.get("declarado_kg") or 0)
        pct = abs(dif) / declarado * 100 if declarado else 0.0
        art = arts.get(c.get("codigo")) or {}
        costo = float(art.get("costo_iva") or 0)
        item = {
            "numero": c.get("numero"),
            "fecha": c.get("fecha"),
            "codigo": c.get("codigo"),
            "lote": c.get("lote"),
            "producto": c.get("producto"),
            "variedad": art.get("variedad"),
            "ubicacion": c.get("ubicacion"),
            "ubicacion_id": c.get("ubicacion_id"),
            "camara": c.get("camara"),
            "declarado_kg": round(declarado, 1),
            "fisico_kg": round(float(c.get("fisico_kg") or 0), 1),
            "diferencia_kg": round(dif, 1),
            "diferencia_bolsones": round(dif / 1000, 2),
            "diferencia_pct": round(pct, 2),
            "impacto_pesos": round(abs(dif) * costo, 2),
            "contado_por": c.get("contado_por"),
            "signo": "faltan" if dif < 0 else "sobran",
        }
        if c.get("nota"):
            item["nota_conteo"] = c["nota"]
        item["hipotesis"] = hipotesis(item, umbral_pct, regla)
        if not incluir_explicadas and item["hipotesis"]["clase"] == "tara":
            continue
        out.append(item)
    out.sort(key=lambda x: -x["impacto_pesos"])
    return out


def abiertas() -> list[dict]:
    """Las que necesitan que alguien haga algo (la tara no cuenta)."""
    return [d for d in diferencias() if d["hipotesis"]["clase"] != "tara"]


# ---------------------------------------------------------------------------
# La hipótesis
# ---------------------------------------------------------------------------
def hipotesis(dif: dict, umbral_pct: float | None = None,
              regla: dict | None = None) -> dict:
    """La causa más probable de UNA diferencia, buscada en los datos.

    Devuelve siempre la misma forma: `clase` (para que la UI decida el color y
    la acción), `confianza`, `texto` (armado por plantilla, no por el modelo) y
    `evidencia` (los objetos reales que la sostienen, para que cualquiera pueda
    ir a verificarlos)."""
    if umbral_pct is None:
        umbral_pct, regla = _umbral_tara_pct()
    faltante = -float(dif["diferencia_kg"])      # positivo si faltan kilos

    # --- 4) tara de bolsón: chica y explicada por el oficio ------------------
    if dif["diferencia_pct"] < umbral_pct:
        ev = {"umbral_pct": umbral_pct}
        if regla:
            ev["regla"] = conocimiento.resumen_pieza(regla)
        return {
            "clase": "tara",
            "confianza": "alta",
            "texto": (f"Diferencia de {_kg(dif['diferencia_kg'])} kg sobre "
                      f"{_kg(dif['declarado_kg'])} ({dif['diferencia_pct']:.2f}%): "
                      f"está por debajo del {umbral_pct}% y es tara de bolsón, "
                      f"no faltante."),
            "accion": None,
            "evidencia": ev,
        }

    # --- 1) traslado sin confirmar en destino -------------------------------
    if faltante > 0:
        for m in movimientos.sin_confirmar():
            if m.get("codigo") != dif["codigo"]:
                continue
            if _norm(m.get("origen")) != _norm(dif["ubicacion"]):
                continue
            if abs(float(m.get("kg") or 0) - faltante) > TOLERANCIA_MATCH_KG:
                continue
            f = parse_fecha(m.get("fecha"))
            fecha_txt = f.strftime("%d/%m") if f else str(m.get("fecha"))
            return {
                "clase": "movimiento_sin_confirmar",
                "confianza": "alta",
                "texto": (f"El movimiento {m['numero']} del {fecha_txt} sacó "
                          f"{_kg(m['kg'])} kg de {m['origen']} hacia "
                          f"{m['destino']} y nadie lo confirmó en destino. "
                          f"Son exactamente los kilos que faltan acá: los bolsones "
                          f"probablemente estén en {m['destino']} sin registrar."),
                "accion": {
                    "tipo": "confirmar_movimiento",
                    "numero": m["numero"],
                    "destino": m["destino"],
                    "etiqueta": f"Verificar en {m['destino']} y confirmar",
                },
                "evidencia": {
                    "movimiento": m,
                    "dias_en_transito": m.get("dias_en_transito"),
                    "registrado_por": m.get("registrado_por"),
                },
            }

    # --- 2) cantidad mal tipeada (un cero de más o de menos) ----------------
    recientes = movimientos.listar(lote=dif["lote"], limite=25)
    for m in recientes:
        kg = float(m.get("kg") or 0)
        if kg <= 0:
            continue
        for factor, como in ((10.0, "un cero de más"), (0.1, "un cero de menos")):
            corregido = kg / factor
            # si el movimiento hubiera sido `corregido`, ¿cierra la diferencia?
            if abs((kg - corregido) - (-faltante)) <= TOLERANCIA_MATCH_KG:
                f = parse_fecha(m.get("fecha"))
                fecha_txt = f.strftime("%d/%m") if f else str(m.get("fecha"))
                return {
                    "clase": "cantidad_mal_tipeada",
                    "confianza": "media",
                    "texto": (f"El movimiento {m['numero']} del {fecha_txt} registró "
                              f"{_kg(kg)} kg. Si en realidad hubieran sido "
                              f"{_kg(corregido)} — {como} al cargarlo — la cámara "
                              f"cerraría exacta. Lo cargó {m.get('registrado_por')} "
                              f"por {m.get('canal')}."),
                    "accion": {
                        "tipo": "corregir_movimiento",
                        "numero": m["numero"],
                        "kg_sugerido": round(corregido, 1),
                        "etiqueta": f"Corregir a {_kg(corregido)} kg",
                    },
                    "evidencia": {"movimiento": m, "kg_registrado": kg,
                                  "kg_sugerido": round(corregido, 1)},
                }

    # --- 3) merma física con testigo ----------------------------------------
    if faltante > 0:
        testigo = _nota_que_explica(dif)
        if testigo:
            return {
                "clase": "merma_fisica",
                "confianza": "media",
                "texto": (f"Faltan {_kg(faltante)} kg y no hay ningún movimiento que "
                          f"los explique. {testigo['autor'].capitalize()} anotó el "
                          f"{_fecha_corta(testigo['fecha'])}: «{testigo['texto']}» — "
                          f"puede ser pérdida física, no un error de registro."),
                "accion": {
                    "tipo": "registrar_descarte",
                    "codigo": dif["codigo"],
                    "kg": round(faltante, 1),
                    "etiqueta": f"Dar de baja {_kg(faltante)} kg por merma",
                },
                "evidencia": {"nota": testigo},
            }

    # --- 5) sin causa en los datos ------------------------------------------
    return {
        "clase": "sin_explicacion",
        "confianza": "baja",
        "texto": (f"{'Faltan' if faltante > 0 else 'Sobran'} "
                  f"{_kg(dif['diferencia_kg'])} kg en {dif['ubicacion']} "
                  f"({dif['camara']}) y no encuentro nada en los datos que lo "
                  f"explique: ningún movimiento sin confirmar, ninguna carga mal "
                  f"tipeada y ninguna nota del equipo sobre este lote. Hay que ir "
                  f"a contarlo de nuevo."),
        "accion": {
            "tipo": "recontar",
            "codigo": dif["codigo"],
            "ubicacion": dif["ubicacion"],
            "etiqueta": f"Pedir recuento en {dif['camara']}",
        },
        "evidencia": {"buscado_en": ["movimientos en tránsito", "cargas del lote",
                                     "notas del equipo"]},
    }


def _kg(x: float) -> str:
    """18000 → "18.000". Formatea SÓLO el número: el texto de la oración se
    arma aparte, así una coma de la prosa nunca se convierte en punto."""
    return f"{abs(float(x)):,.0f}".replace(",", ".")


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def _fecha_corta(f: str) -> str:
    d = parse_fecha(f)
    return d.strftime("%d/%m") if d else str(f)


def _nota_que_explica(dif: dict) -> dict | None:
    """Una nota del equipo que hable de este lote, de esta cámara o de esta
    ubicación, y que mencione algo que hace perder kilos.

    Es la mitad que no está en ninguna planilla: alguien lo dijo, nadie lo
    cargó, y la explicación estaba ahí desde el principio."""
    pistas = ("brot", "pudri", "temperatura", "grados", "merma", "perd", "se ech")
    camara = _norm(dif.get("camara"))
    ubic = _norm(dif.get("ubicacion"))
    variedad = _norm(dif.get("variedad"))
    candidatas = []
    for n in notas.listar():
        t = _norm(n.get("texto"))
        if not any(p in t for p in pistas):
            continue
        toca = ((camara and camara in t)
                or (variedad and variedad in t)
                or (ubic and any(w in t for w in ubic.split() if len(w) > 4)))
        if toca:
            candidatas.append(n)
    if not candidatas:
        return None
    candidatas.sort(key=lambda n: str(n.get("fecha") or ""), reverse=True)
    return candidatas[0]


# ---------------------------------------------------------------------------
# El tablero — la vista única de las cuatro ubicaciones
# ---------------------------------------------------------------------------
def por_ubicacion() -> list[dict]:
    """El estado de cada una de las cuatro ubicaciones, en una sola lectura.

    Esto es lo que hoy no existe: una persona que quiera saber cuánto hay en
    Batán tiene que abrir la planilla, filtrar, y confiar en que nadie la editó
    mientras tanto."""
    arts = store.raw_actual()
    difs = abiertas()
    h = hoy()
    out = []
    for u in semilla.ubicaciones():
        lotes = [a for a in arts if a.get("ubicacion_id") == u["id"]]
        kg = sum(float(a.get("stock") or 0) for a in lotes)
        valor = sum(float(a.get("stock") or 0) * float(a.get("costo_iva") or 0)
                    for a in lotes)
        d_aqui = [d for d in difs if d["ubicacion_id"] == u["id"]]
        # El reloj real de la semilla, en DOS listas que no son lo mismo:
        # lo que se brota pronto (todavía se puede hacer algo) y lo que ya
        # brotó (dejó de ser semilla de su categoría). Mezclarlas hace que la
        # pantalla diga "se brotan pronto" y muestre cosas que ya pasaron.
        por_brotar, ya_brotados = [], []
        for a in lotes:
            b = parse_fecha(a.get("brotacion_estimada"))
            if not b:
                continue
            dd = (b - h).days
            item = {"codigo": a.get("codigo"), "lote": a.get("lote"),
                    "dias": dd, "kg": float(a.get("stock") or 0),
                    "valor": round(float(a.get("stock") or 0)
                                   * float(a.get("costo_iva") or 0), 2)}
            if dd <= 0:
                ya_brotados.append(item)
            elif dd <= 45:
                por_brotar.append(item)
        por_brotar.sort(key=lambda x: x["dias"])
        ya_brotados.sort(key=lambda x: -x["valor"])
        cap = float(u.get("capacidad_kg") or 0)
        out.append({
            "id": u["id"],
            "nombre": u["nombre"],
            "tipo": u["tipo"],
            "camaras": u.get("camaras") or [],
            "direccion": u.get("direccion"),
            "temp_objetivo": u.get("temp_objetivo"),
            "lotes": len(lotes),
            "kg": round(kg, 1),
            "toneladas": round(kg / 1000, 1),
            "bolsones": round(kg / 1000, 1),
            "capacidad_kg": cap,
            "ocupacion_pct": round(kg / cap * 100, 1) if cap else None,
            "valor": round(valor, 2),
            "diferencias_abiertas": len(d_aqui),
            "kg_en_diferencia": round(sum(abs(d["diferencia_kg"]) for d in d_aqui), 1),
            "por_brotar_45d": por_brotar[:5],
            "ya_brotados": len(ya_brotados),
            "ya_brotados_valor": round(sum(x["valor"] for x in ya_brotados), 2),
            "estado": ("rojo" if any(d["hipotesis"]["clase"] == "sin_explicacion"
                                     for d in d_aqui)
                       else "amarillo" if d_aqui else "verde"),
        })
    return out


def resumen() -> dict:
    """El titular: cuánto stock hay en total, cuánto está en discusión y dónde."""
    ubis = por_ubicacion()
    difs = abiertas()
    mov = movimientos.resumen()
    kg_total = sum(u["kg"] for u in ubis)
    return {
        "hay_datos": hay_datos(),
        "ubicaciones": len(ubis),
        "lotes": sum(u["lotes"] for u in ubis),
        "kg_total": round(kg_total, 1),
        "toneladas_total": round(kg_total / 1000, 1),
        "valor_total": round(sum(u["valor"] for u in ubis), 2),
        "conteos": len(_conteos()),
        "diferencias_abiertas": len(difs),
        "kg_en_diferencia": round(sum(abs(d["diferencia_kg"]) for d in difs), 1),
        "plata_en_diferencia": round(sum(d["impacto_pesos"] for d in difs), 2),
        "sin_explicacion": sum(1 for d in difs
                               if d["hipotesis"]["clase"] == "sin_explicacion"),
        "movimientos_sin_confirmar": mov["sin_confirmar"],
        "kg_en_transito": mov["kg_en_transito"],
    }
