"""
mapa_real.py · El mapa de la operación como es, no como lo imaginamos.

EL ERROR QUE ESTE MÓDULO VIENE A CORREGIR

El mapa anterior dibujaba cuatro depósitos y los lotes yendo directo del campo
al frío. Un empleado de Papasud lo detecta en dos segundos, porque **falta la
planta**. Textual de la charla:

    «El camión viene a Mar del Plata, entra a la planta, pasa a una primera
     recepción. Se baja a la báscula, el camión pesa, el que recibe toma el peso
     y los datos de la mercadería: camionero, quién es, qué camión, producto,
     todo. Y lo vuelca a la primera planilla de recepción.»

La planta es donde **nace el dato**. Todo lo que el sistema sabe después
arranca en esa báscula. Y la venta sale de ahí:

    «Lote → planta → cliente. O llega a la planta y de la planta va al cliente.
     Muchas veces la papa puede salir del lote que está en el campo, va a la
     planta, va al frigorífico, VUELVE A LA PLANTA y sale al cliente. Eso es
     muy común.»

LAS CUATRO COLUMNAS

    CAMPOS          →      PLANTA MDP      ⇄      FRIGORÍFICOS   →   CLIENTES
    pivote                 (la báscula)           subcontratados
    cuadrante                                     se les paga
    lote (1 variedad)                             por kilo movido

El ida y vuelta **planta ⇄ frigorífico** se dibuja como dos flechas separadas,
una arriba y otra abajo, porque es el circuito que más usan y el que hoy peor
siguen. Una sola línea con dos puntas lo esconde.

POR QUÉ NO CONTRADICE EL BRIEF

El brief dice «cuatro ubicaciones, una sola verdad» y habla de tres frigoríficos
y un galpón. Sigue siendo cierto: **las ubicaciones que GUARDAN stock** son
ésas. Los campos son de dónde sale y los clientes adónde va — no guardan nada.
Lo que agregamos es el eslabón que faltaba en el medio, y el contador de
ubicaciones sigue contando sólo las que guardan.

TODO SALE DEL LIBRO
Ningún número de acá se calcula dos veces. Los nodos leen `disponibilidad`, que
lee el libro de movimientos que salió de la planilla. Si el mapa dice 244.362 kg
en Dospanca, la pantalla de disponibilidad dice lo mismo, porque es el mismo
cálculo.
"""
from __future__ import annotations

from collections import defaultdict

from . import disponibilidad as disp
from . import papasud_real as real
from .fechas import hoy, parse_fecha

# Cuántos clientes entran en la columna antes de agrupar el resto. Más de seis
# nombres apilados no se leen desde el fondo de la sala.
TOP_CLIENTES = 6

CAPAS = [
    {"id": "campo", "titulo": "De dónde sale",
     "detalle": "Campos, pivotes y cuadrantes. Cada lote, una sola variedad."},
    {"id": "planta", "titulo": "Por dónde pasa todo",
     "detalle": "Planta Mar del Plata. Acá está la báscula: el camión se pesa y "
                "nace el registro. La venta sale de acá."},
    {"id": "frio", "titulo": "Dónde se guarda",
     "detalle": "Frigoríficos subcontratados. Se les paga por kilo movido, por eso "
                "cada movimiento se trackea por lugar."},
    {"id": "cliente", "titulo": "Adónde va",
     "detalle": "Mercado interno y exportación."},
]

# Qué solapa alimenta cada tramo del circuito.
TRAMOS = {
    "ingreso_tolva": ("campo", "planta", "ingreso"),
    "ingreso_multiplicacion": ("campo", "planta", "ingreso"),
    "campo_a_frio": ("campo", "frio", "directo_a_frio"),
    "envio_a_frio": ("planta", "frio", "ida"),
    "retiro_de_frio": ("frio", "planta", "vuelta"),
    "entrega_cliente": (None, "cliente", "venta"),
}


def _num(v) -> str:
    return f"{round(v or 0):,}".replace(",", ".")


def _dias(iso: str | None) -> int | None:
    d = parse_fecha(iso)
    return None if not d else (hoy() - d).days


# ===========================================================================
# LOS NODOS
# ===========================================================================
def _campos() -> list[dict]:
    """Un nodo por campo, con sus lotes adentro. El campo no guarda stock: es
    de donde SALIÓ. Su número es lo que mandó, no lo que tiene."""
    por_campo: dict[str, dict] = {}
    for m in real.movimientos():
        o = m.get("origen") or {}
        if o.get("tipo") != "lote":
            continue
        lote = real.lote_por_id().get(o["id"]) or {}
        cid = lote.get("campo") or "sin_declarar"
        c = por_campo.setdefault(cid, {
            "kg": 0, "lotes": set(), "variedades": set(), "viajes": set(),
            "pivotes": defaultdict(set),
        })
        c["kg"] += m.get("kg") or 0
        c["lotes"].add(o["id"])
        if m.get("variedad"):
            c["variedades"].add(m["variedad"])
        c["viajes"].add(m.get("remito_id") or m["id"])
        if lote.get("pivote"):
            c["pivotes"][lote["pivote"]].add(o["id"])

    nombres = {c["id"]: c["nombre"] for c in real.campos()}
    nodos = []
    for cid, c in sorted(por_campo.items(), key=lambda kv: -kv[1]["kg"]):
        sin_declarar = cid == "sin_declarar"
        nodos.append({
            "id": f"campo:{cid}",
            "tipo": "campo", "capa": "campo",
            "etiqueta": "Sin campo declarado" if sin_declarar else nombres.get(cid, cid.title()),
            "kg": round(c["kg"]),
            "lotes": len(c["lotes"]),
            "variedades": sorted(c["variedades"]),
            "viajes": len(c["viajes"]),
            "pivotes": {p: len(ls) for p, ls in sorted(c["pivotes"].items())},
            "alerta": sin_declarar,
            "subtitulo": (f"{len(c['lotes'])} lotes que la planilla no dice de "
                          f"qué campo salen" if sin_declarar
                          else f"{len(c['lotes'])} lotes · {len(c['variedades'])} variedades"),
        })
    return nodos


def _ubicacion(uid: str, capa: str) -> dict:
    """Un nodo que SÍ guarda stock. Su número es lo que tiene hoy."""
    ps = disp.partidas(ubicacion=uid)
    r = disp.resumen(ps)
    u = real.ubicacion_por_id().get(uid, {})
    comp = disp.comprometido(ubicacion=uid)

    # Lo más viejo que está guardado ahí. En una cámara importa: la semilla no
    # vence, brota — y lo que lleva meses es lo primero que hay que sacar.
    dias = [d for d in (_dias(p["fecha"]) for p in ps) if d is not None]
    return {
        "id": f"ubic:{uid}",
        "tipo": u.get("tipo") or "frigorifico", "capa": capa,
        "ubicacion": uid,
        "etiqueta": real.nombre_ubicacion(uid),
        "kg": r["kg"], "bolsas": r["bolsas"], "kg_granel": r.get("kg_granel", 0),
        "lotes": len(r["por_lote"]),
        "variedades": [{"variedad": v["clave"], "kg": v["kg"]}
                       for v in r["por_variedad"][:6]],
        "comprometido": comp["kg"],
        "libre": max(0, r["kg"] - comp["kg"]),
        "saldo_anterior_kg": r["saldo_anterior_kg"],
        "propia": bool(u.get("propia")),
        "bascula": bool(u.get("bascula")),
        "dias_mas_viejo": max(dias) if dias else None,
        "subtitulo": _subtitulo_ubicacion(u, r, comp),
    }


def _subtitulo_ubicacion(u: dict, r: dict, comp: dict) -> str:
    if u.get("bascula"):
        return "acá se pesa: el camión entra, la báscula manda"
    if not u.get("propia"):
        return "frigorífico subcontratado — se paga por kilo movido"
    return f"{len(r['por_lote'])} lotes"


def _clientes() -> list[dict]:
    por_cliente: dict[str, dict] = {}
    for m in real.movimientos():
        d = m.get("destino") or {}
        if d.get("tipo") != "cliente":
            continue
        c = por_cliente.setdefault(d["id"], {"kg": 0, "viajes": set(),
                                             "variedades": set()})
        c["kg"] += m.get("kg") or 0
        c["viajes"].add(m.get("remito_id") or m["id"])
        if m.get("variedad"):
            c["variedades"].add(m["variedad"])

    orden = sorted(por_cliente.items(), key=lambda kv: -kv[1]["kg"])
    nodos = []
    for cid, c in orden[:TOP_CLIENTES]:
        nodos.append({
            "id": f"cliente:{cid}", "tipo": "cliente", "capa": "cliente",
            "etiqueta": cid.title(), "kg": round(c["kg"]),
            "viajes": len(c["viajes"]), "variedades": sorted(c["variedades"]),
            "subtitulo": f"{len(c['viajes'])} camiones",
        })
    resto = orden[TOP_CLIENTES:]
    if resto:
        nodos.append({
            "id": "cliente:otros", "tipo": "cliente_grupo", "capa": "cliente",
            "etiqueta": f"otros {len(resto)} clientes",
            "kg": round(sum(c["kg"] for _, c in resto)),
            "viajes": sum(len(c["viajes"]) for _, c in resto),
            "clientes": [k for k, _ in resto],
            "subtitulo": "los que compran menos volumen",
        })
    return nodos


# ===========================================================================
# LAS ARISTAS — el circuito real
# ===========================================================================
def _nodo_de(nodo: dict | None, lote_a_campo: dict) -> str | None:
    if not nodo:
        return None
    if nodo["tipo"] == "lote":
        campo = lote_a_campo.get(nodo["id"]) or "sin_declarar"
        return f"campo:{campo}"
    if nodo["tipo"] == "cliente":
        return f"cliente:{nodo['id']}"
    if nodo["tipo"] in ("planta", "galpon", "frigorifico"):
        return f"ubic:{nodo['id']}"
    if nodo["tipo"] == "campo":
        return f"campo:{nodo['id']}"
    return None


def _clase(nid: str) -> str:
    if nid.startswith("campo:"):
        return "campo"
    if nid.startswith("cliente:"):
        return "cliente"
    if nid == "sin_destino":
        return "vacio"
    tipo = (real.ubicacion_por_id().get(nid[5:], {}) or {}).get("tipo")
    return "planta" if tipo == "planta" else ("galpon" if tipo == "galpon" else "frio")


def _sentido(o: str, d: str) -> str:
    a, b = _clase(o), _clase(d)
    if b == "cliente":
        return "venta_directa" if a == "campo" else "venta"
    if a == "campo":
        return "ingreso" if b == "planta" else "directo_a_frio"
    if a == "planta" and b in ("frio", "galpon"):
        return "ida"
    if a in ("frio", "galpon") and b == "planta":
        return "vuelta"
    if a in ("frio", "galpon") and b in ("frio", "galpon"):
        return "entre_frios"
    return "otro"


def _aristas(ids_validos: set[str], otros_clientes: set[str]) -> list[dict]:
    lote_a_campo = {l["id"]: l.get("campo") for l in real.lotes()}
    g: dict[tuple, dict] = {}

    for m in real.movimientos():
        kg = m.get("kg") or 0
        if not kg or m.get("reingresa"):
            continue
        o = _nodo_de(m.get("origen"), lote_a_campo)
        d = _nodo_de(m.get("destino"), lote_a_campo)
        # Los clientes chicos entran todos por el nodo agrupado.
        if d and d.startswith("cliente:") and d not in ids_validos:
            d = "cliente:otros" if d[8:] in otros_clientes else None
        if not o or not d or o == d:
            continue
        if o not in ids_validos or d not in ids_validos:
            continue
        # El sentido sale de DÓNDE va, no de qué solapa vino. Un retiro de frío
        # que termina en Paraguay no es una «vuelta a planta»: es una venta que
        # salió de la cámara. La solapa dice cómo lo anotaron; el mapa tiene que
        # decir qué pasó.
        sentido = _sentido(o, d)
        k = (o, d, sentido)
        a = g.setdefault(k, {
            "id": f"{o}__{d}__{sentido}", "origen": o, "destino": d,
            "sentido": sentido, "kg": 0, "viajes": set(),
            "kg_sin_destino": 0, "sin_destino": 0,
        })
        a["kg"] += kg
        a["viajes"].add(m.get("remito_id") or m["id"])

    # Los kilos que salieron de una cámara y la planilla no dice adónde fueron.
    # No es un tramo: es un agujero, y va colgado del frigorífico que los soltó.
    for m in real.movimientos():
        if m.get("tipo") != "retiro_de_frio" or m.get("destino"):
            continue
        o = _nodo_de(m.get("origen"), lote_a_campo)
        if not o or o not in ids_validos:
            continue
        k = (o, "sin_destino", "perdido")
        a = g.setdefault(k, {
            "id": f"{o}__sin_destino", "origen": o, "destino": "sin_destino",
            "sentido": "perdido", "kg": 0, "viajes": set(),
            "kg_sin_destino": 0, "sin_destino": 0,
        })
        a["kg_sin_destino"] += m.get("kg") or 0
        a["sin_destino"] += 1
        a["viajes"].add(m.get("remito_id") or m["id"])

    out = []
    for a in g.values():
        a["viajes"] = len(a["viajes"])
        a["kg"] = round(a["kg"])
        a["kg_sin_destino"] = round(a["kg_sin_destino"])
        out.append(a)
    return sorted(out, key=lambda a: -(a["kg"] + a["kg_sin_destino"]))


# ===========================================================================
# LOS HALLAZGOS — agrupados, con jerarquía, y cada uno ilumina su camino
# ===========================================================================
# No valen todos lo mismo. Una venta que se va a caer no es «50 kg sobran».
GRAVEDAD = {
    "venta_frenada": "grave",
    "destino_no_declarado": "grave",
    "lote_multivariedad": "grave",
    "kg_prom_contradice": "grave",
    "tarjeta_cruzada": "grave",
    "nota_al_margen": "grave",
    "kg_prom_imposible": "atencion",
    "kg_bolsa_fuera_del_historico": "atencion",
    "sin_remito": "atencion",
    "dtv_repetido": "atencion",
    "saldo_anterior": "atencion",
    "sin_dtv": "menor",
    "columna_con_otro_dato": "menor",
    "lote_sin_campo": "menor",
    "nombre_escrito_distinto": "menor",
    "kg_como_texto": "menor",
    "dtv_en_columna_ajena": "menor",
}
ORDEN_GRAVEDAD = {"grave": 0, "atencion": 1, "menor": 2}

# Seis familias, no diecisiete tipos sueltos. Un encargado piensa en «kilos que
# no sé dónde están», no en `destino_no_declarado`.
FAMILIAS = [
    {"id": "ventas", "titulo": "Ventas que se van a caer",
     "tipos": ["venta_frenada"],
     "que_significa": "hay pedidos comprometidos por encima de lo que hay libre"},
    {"id": "kilos_en_el_aire", "titulo": "Kilos sin dónde",
     "tipos": ["destino_no_declarado", "saldo_anterior"],
     "que_significa": "salieron de una cámara y el libro no dice adónde fueron"},
    {"id": "no_cierra", "titulo": "Números que no cierran",
     "tipos": ["kg_prom_contradice", "kg_prom_imposible",
               "kg_bolsa_fuera_del_historico"],
     "que_significa": "los kilos, las bolsas y el peso por bolsa se contradicen"},
    {"id": "identidad", "titulo": "Lote e identificación cruzados",
     "tipos": ["tarjeta_cruzada", "nota_al_margen", "lote_multivariedad"],
     "que_significa": "la tarjeta o la variedad no coinciden con el lote declarado"},
    {"id": "papeles", "titulo": "Papeles que faltan",
     "tipos": ["sin_dtv", "sin_remito", "dtv_repetido", "dtv_en_columna_ajena"],
     "que_significa": "movimientos sin el documento que los ampara"},
    {"id": "carga", "titulo": "Cargado en el lugar equivocado",
     "tipos": ["columna_con_otro_dato", "lote_sin_campo",
               "nombre_escrito_distinto", "kg_como_texto"],
     "que_significa": "el dato existe pero está en una columna que no es la suya"},
]


def _ventas_frenadas() -> list[dict]:
    """Pedidos abiertos que ya no entran en lo que hay libre.

    Es el hallazgo más caro de todos y el único que se puede evitar hoy: la
    venta todavía no se cayó. Es exactamente lo que pidieron — que la alerta
    salte ANTES, no cuando el camión está en la playa.
    """
    out = []
    for p in disp.pedidos_abiertos():
        ev = disp.consultar(variedad=p.get("variedad"), calibre=p.get("calibre"),
                            ubicacion=p.get("ubicacion"))
        pedido_kg = disp._kg_pedido(p)
        # Lo libre ya descuenta ESTE pedido: se lo devolvemos para preguntar si
        # el stock alcanza a cubrirlo.
        disponible = ev["hay"] - (ev["comprometido"] - pedido_kg)
        if disponible >= pedido_kg:
            continue
        # Si lo que hay está sin clasificar, el pedido no está perdido: está a
        # una pasada por la clasificadora. Decirlo cambia la acción de «avisale
        # al cliente» a «metelo en la máquina».
        sc = sum(x["kg"] for x in disp.partidas(variedad=p.get("variedad"),
                                                ubicacion=p.get("ubicacion"))
                 if x["calibre"] == disp.SIN_CLASIFICAR)
        matiz = (f" Hay {_num(sc)} kg de esa variedad ahí, sin clasificar."
                 if p.get("calibre") and sc else "")
        out.append({
            "id": f"venta_frenada:{p['id']}",
            "tipo": "venta_frenada",
            "titulo": f"{p['cliente'].title()} no entra",
            "detalle": (f"{_num(pedido_kg)} kg de {p['variedad']}"
                        f"{' ' + p['calibre'] if p.get('calibre') else ''} para el "
                        f"{p.get('entrega') or 'sin fecha'} en "
                        f"{real.nombre_ubicacion(p.get('ubicacion'))}, y hay "
                        f"{_num(max(0, disponible))} kg. "
                        f"Faltan {_num(pedido_kg - disponible)} kg.{matiz}"),
            "kg": round(pedido_kg - disponible),
            "nodos": [f"ubic:{p['ubicacion']}"] if p.get("ubicacion") else [],
            "pedido": p,
            "accion": "buscar_alternativa",
        })
    return out


def hallazgos() -> dict:
    """Todo lo que está mal, agrupado por familia y ordenado por gravedad."""
    anom = real.anomalias()
    libro = disp.libro()

    # Cada anomalía cuelga del nodo donde se ve. Tocar el hallazgo ilumina el
    # camino en el lienzo: es la diferencia entre una lista y un mapa.
    por_mov = {m["id"]: m for m in real.movimientos()}
    lote_a_campo = {l["id"]: l.get("campo") for l in real.lotes()}

    items: list[dict] = list(_ventas_frenadas())

    # Un saldo anterior por MOVIMIENTO son ciento cincuenta líneas iguales. Por
    # UBICACIÓN son cinco hallazgos que se leen. La evidencia de cada uno queda
    # adentro, sin perder ni una fila.
    por_ubic: dict[str, list] = defaultdict(list)
    for s in libro["saldos_anteriores"]:
        por_ubic[s["ubicacion"]].append(s)
    for uid, ss in por_ubic.items():
        kg = sum(x["kg"] for x in ss)
        lotes = sorted({x["lote"] for x in ss if x.get("lote")})
        items.append({
            "id": f"saldo_anterior:{uid}",
            "tipo": "saldo_anterior",
            "titulo": f"{_num(kg)} kg sin respaldo en {real.nombre_ubicacion(uid)}",
            "detalle": (f"{len(ss)} retiros sacaron mercadería de "
                        f"{real.nombre_ubicacion(uid)} que esta planilla no "
                        f"registra que haya entrado. Son {len(lotes)} lotes: "
                        f"{', '.join(lotes[:8])}"
                        f"{'…' if len(lotes) > 8 else ''}. Entró antes de febrero."),
            "kg": round(kg),
            "nodos": [f"ubic:{uid}"],
            "evidencia": ss[:20],
            "fuente": ss[0].get("fuente"),
        })

    for a in anom:
        mov = por_mov.get(a.get("movimiento") or "")
        nodos = []
        if mov:
            for lado in ("origen", "destino"):
                n = _nodo_de(mov.get(lado), lote_a_campo)
                if n:
                    nodos.append(n)
        items.append({
            "id": f"{a['id']}:{a.get('movimiento') or a.get('valor')}",
            "tipo": a["id"],
            "titulo": _titulo_anomalia(a, mov),
            "detalle": a["detalle"],
            "kg": (mov or {}).get("kg") or 0,
            "nodos": nodos,
            "fuente": a.get("fuente"),
            "movimiento": a.get("movimiento"),
        })

    for it in items:
        it["gravedad"] = GRAVEDAD.get(it["tipo"], "menor")

    familias = []
    for prioridad, f in enumerate(FAMILIAS):
        propios = [i for i in items if i["tipo"] in f["tipos"]]
        if not propios:
            continue
        propios.sort(key=lambda i: (ORDEN_GRAVEDAD[i["gravedad"]], -(i["kg"] or 0)))
        gravedad = min((i["gravedad"] for i in propios), key=lambda g: ORDEN_GRAVEDAD[g])
        familias.append({
            **{k: v for k, v in f.items() if k != "tipos"},
            "prioridad": prioridad,
            "gravedad": gravedad,
            "cantidad": len(propios),
            "kg": round(sum(i["kg"] or 0 for i in propios)),
            "destacado": propios[0],
            "items": propios[:60],
        })
    familias.sort(key=lambda f: (ORDEN_GRAVEDAD[f["gravedad"]], f["prioridad"]))
    return {
        "familias": familias,
        "total": len(items),
        "graves": sum(1 for i in items if i["gravedad"] == "grave"),
    }


def _titulo_anomalia(a: dict, mov: dict | None) -> str:
    f = a.get("fuente") or {}
    donde = (f"{f.get('solapa')} · fila {f.get('fila_excel')}"
             if f.get("fila_excel") else "varias filas")
    titulos = {
        "destino_no_declarado": "Un retiro sin destino",
        "lote_multivariedad": f"El lote {(mov or {}).get('lote', '')} declara dos variedades",
        "kg_prom_contradice": "La fila se contradice a sí misma",
        "kg_prom_imposible": "El peso por bolsa no existe",
        "kg_bolsa_fuera_del_historico": "Se aparta del histórico del lote",
        "tarjeta_cruzada": "La tarjeta no es la del lote",
        "nota_al_margen": "Una anotación a mano que nadie cruzó",
        "sin_remito": "Movimiento sin remito",
        "sin_dtv": "Movimiento sin DTV",
        "dtv_repetido": "Un DTV para dos remitos",
        "columna_con_otro_dato": "Un dato en la columna equivocada",
        "lote_sin_campo": "Un lote que no dice de qué campo sale",
        "nombre_escrito_distinto": "La misma persona, dos nombres",
        "kg_como_texto": "Kilos escritos como texto",
        "dtv_en_columna_ajena": "Un DTV donde va otra cosa",
    }
    return f"{titulos.get(a['id'], a['id'])} — {donde}"


# ===========================================================================
def mapa() -> dict:
    campos = _campos()
    ubis = real.ubicaciones()
    planta = [_ubicacion(u["id"], "planta") for u in ubis
              if u["tipo"] in ("planta", "galpon")]
    frios = sorted([_ubicacion(u["id"], "frio") for u in ubis
                    if u["tipo"] == "frigorifico"],
                   key=lambda n: -n["kg"])
    clientes = _clientes()

    nodos = campos + planta + frios + clientes
    ids = {n["id"] for n in nodos}
    otros = set()
    for n in clientes:
        if n["id"] == "cliente:otros":
            otros = set(n["clientes"])
    aristas = _aristas(ids | {"sin_destino"}, otros)

    guardan = [n for n in nodos if n["capa"] in ("planta", "frio")]
    kg_stock = sum(n["kg"] for n in guardan)
    sin_destino = sum(a["kg_sin_destino"] for a in aristas)
    h = hallazgos()

    return {
        "capas": CAPAS,
        "nodos": nodos,
        "aristas": aristas,
        "hallazgos": h,
        "resumen": {
            "toneladas": round(kg_stock / 1000, 1),
            "kg": kg_stock,
            "lotes": len(real.lotes()),
            # El brief cuenta las ubicaciones que GUARDAN. Campos y clientes no
            # guardan: son de dónde sale y adónde va.
            "ubicaciones": len(guardan),
            "campos": len(campos),
            "kg_sin_destino": sin_destino,
            "movimientos_sin_destino": sum(a["sin_destino"] for a in aristas),
            "hallazgos": h["total"],
            "graves": h["graves"],
            "comprometido": disp.comprometido()["kg"],
            "movimientos": len(real.movimientos()),
        },
    }


# ===========================================================================
# EL DETALLE DE UN NODO — el panel que se abre sin mover la cámara
# ===========================================================================
def detalle(nid: str) -> dict | None:
    if nid.startswith("campo:"):
        return _detalle_campo(nid.split(":", 1)[1])
    if nid.startswith("ubic:"):
        return _detalle_ubicacion(nid.split(":", 1)[1])
    if nid.startswith("cliente:"):
        return _detalle_cliente(nid.split(":", 1)[1])
    if nid.startswith("lote:"):
        return detalle_lote(nid.split(":", 1)[1])
    return None


def _detalle_campo(cid: str) -> dict:
    """Los pivotes, los cuadrantes y los lotes, con la variedad de cada uno.

    La regla se ve acá: cada lote muestra UNA variedad. El que declara dos sale
    en rojo, porque eso es un error del dato, no una característica del lote.
    """
    lotes = [l for l in real.lotes()
             if (l.get("campo") or "sin_declarar") == cid]
    filas = []
    for l in sorted(lotes, key=lambda l: l["id"]):
        ps = disp.partidas(lote=l["id"])
        filas.append({
            "lote": l["id"],
            "variedad": l.get("variedad"),
            "variedades_en_conflicto": l.get("variedades_en_conflicto") or [],
            "pivote": l.get("pivote"),
            "cuadrante": l.get("cuadrante"),
            "categoria": l.get("categoria"),
            "kg_en_stock": round(sum(p["kg"] for p in ps)),
            "movimientos": l.get("movimientos"),
            "kg_prom": l.get("kg_prom"),
            "evidencia_campo": l.get("evidencia_campo"),
        })
    nombres = {c["id"]: c["nombre"] for c in real.campos()}
    pivotes: dict[str, list] = defaultdict(list)
    for f in filas:
        pivotes[f["pivote"] or "sin pivote declarado"].append(f["lote"])
    return {
        "tipo": "campo", "id": f"campo:{cid}",
        "titulo": nombres.get(cid, "Sin campo declarado"),
        "lotes": filas,
        "pivotes": {p: sorted(ls) for p, ls in sorted(pivotes.items())},
        "nota": ("Estos lotes no declaran campo en la planilla. Asignarles uno "
                 "a ojo sería inventar de dónde salió la mercadería."
                 if cid == "sin_declarar" else None),
    }


def _detalle_ubicacion(uid: str) -> dict:
    """Qué hay guardado, de qué lotes y desde cuándo.

    Para la planta, además: la última jornada de báscula. El dataset termina el
    11/08 — decir «hoy» cuando el último camión entró hace once días sería
    mostrar un cero que no es cierto, así que se dice qué día fue.
    """
    ps = disp.partidas(ubicacion=uid)
    r = disp.resumen(ps)
    u = real.ubicacion_por_id().get(uid, {})

    lotes = []
    for g in r["por_lote"]:
        del_lote = [p for p in ps if p["lote"] == g["clave"]]
        dias = [d for d in (_dias(p["fecha"]) for p in del_lote) if d is not None]
        lotes.append({
            "lote": g["clave"],
            "variedad": (del_lote[0]["variedad"] if del_lote else None),
            "kg": g["kg"], "bolsas": g["bolsas"],
            "calibres": sorted({p["calibre"] for p in del_lote}),
            "remitos": g["remitos"][:6],
            "dias_guardado": max(dias) if dias else None,
            "colores": sorted({f"{p['bolsa_color'] or '?'}/{p['hilo_color'] or '?'}"
                               for p in del_lote if p["bolsa_color"]}),
            "anomalias": g.get("anomalias") or [],
        })

    entradas = [m for m in real.movimientos()
                if (m.get("destino") or {}).get("id") == uid]
    salidas = [m for m in real.movimientos()
               if (m.get("origen") or {}).get("id") == uid]
    ultima = max([m["fecha"] for m in entradas + salidas if m.get("fecha")],
                 default=None)
    jornada = {
        "fecha": ultima,
        "entro": [_linea_mov(m) for m in entradas if m.get("fecha") == ultima],
        "salio": [_linea_mov(m) for m in salidas if m.get("fecha") == ultima],
    }

    return {
        "tipo": u.get("tipo") or "frigorifico", "id": f"ubic:{uid}",
        "titulo": real.nombre_ubicacion(uid),
        "bascula": bool(u.get("bascula")),
        "propia": bool(u.get("propia")),
        "kg": r["kg"], "bolsas": r["bolsas"],
        "saldo_anterior_kg": r["saldo_anterior_kg"],
        "comprometido": disp.comprometido(ubicacion=uid)["kg"],
        "por_variedad": r["por_variedad"],
        "por_calibre": r["por_calibre"],
        "lotes": lotes,
        "ultima_jornada": jornada,
        "movimientos_totales": len(entradas) + len(salidas),
    }


def _linea_mov(m: dict) -> dict:
    return {
        "movimiento": m["id"], "remito": m.get("remito"), "tipo": m.get("tipo"),
        "lote": m.get("lote"), "variedad": m.get("variedad"),
        "kg": m.get("kg"), "bolsas": m.get("bolsas"),
        "transporte": m.get("transporte"), "chofer": m.get("chofer"),
        "dtv": m.get("dtv"), "fecha": m.get("fecha"),
        "desde": real.nombre_nodo(m.get("origen")),
        "hacia": real.nombre_nodo(m.get("destino")),
        "anomalias": m.get("anomalias") or [],
        "fuente": m.get("fuente"),
    }


def _detalle_cliente(cid: str) -> dict:
    from . import comercial
    if cid == "otros":
        v = comercial.ventas()
        return {"tipo": "cliente_grupo", "id": "cliente:otros",
                "titulo": "Los clientes de menos volumen",
                "clientes": comercial.clientes()[TOP_CLIENTES:],
                "kg": v["kg"]}
    v = comercial.ventas(cliente=cid)
    return {
        "tipo": "cliente", "id": f"cliente:{cid}", "titulo": cid.title(),
        "kg": v["kg"], "camiones": v["camiones"],
        "por_variedad": v["por_variedad"], "por_calibre": v["por_calibre"],
        "camion_por_camion": v["camion_por_camion"][:20],
    }


def detalle_lote(lote: str) -> dict | None:
    """El recorrido completo del lote: qué camión lo trajo, cuánto pesó en la
    báscula, a qué frigorífico fue, si volvió, y a quién se vendió.

    Es la pregunta que hoy contestan buscando remito por remito.
    """
    l = real.lote_por_id().get(lote)
    if not l:
        return None
    movs = [m for m in real.movimientos() if m.get("lote") == lote]
    movs.sort(key=lambda m: (m.get("fecha") or "", m["id"]))
    ps = disp.partidas(lote=lote)

    etapas = []
    for m in movs:
        _, _, sentido = TRAMOS.get(m.get("tipo"), (None, None, "otro"))
        etapas.append({**_linea_mov(m), "sentido": sentido,
                       "kg_prom": m.get("kg_prom"),
                       "kg_prom_declarado": m.get("kg_prom_declarado"),
                       "bolsa_color": m.get("bolsa_color"),
                       "hilo_color": m.get("hilo_color"),
                       "observaciones": m.get("observaciones")})

    vendido = sum(m["kg"] or 0 for m in movs if m.get("tipo") == "entrega_cliente")
    clientes = sorted({(m.get("destino") or {}).get("id") for m in movs
                       if m.get("tipo") == "entrega_cliente"} - {None})
    bascula = [m for m in movs if m.get("tipo") in ("ingreso_tolva",
                                                    "ingreso_multiplicacion")]
    return {
        "tipo": "lote", "id": f"lote:{lote}",
        "titulo": f"Lote {lote}",
        "variedad": l.get("variedad"),
        "variedades_en_conflicto": l.get("variedades_en_conflicto") or [],
        "campo": l.get("campo"), "pivote": l.get("pivote"),
        "cuadrante": l.get("cuadrante"), "categoria": l.get("categoria"),
        "kg_prom": l.get("kg_prom"),
        "evidencia_campo": l.get("evidencia_campo"),
        "pesado_en_bascula_kg": round(sum(m["kg"] or 0 for m in bascula)),
        "viajes_a_bascula": len({m.get("remito_id") for m in bascula}),
        "vendido_kg": round(vendido),
        "clientes": clientes,
        "en_stock_kg": round(sum(p["kg"] for p in ps)),
        "donde_esta": [{"ubicacion": real.nombre_ubicacion(u),
                        "kg": round(sum(p["kg"] for p in ps if p["ubicacion"] == u))}
                       for u in sorted({p["ubicacion"] for p in ps})],
        "etapas": etapas,
        "dtvs": sorted({m["dtv"] for m in movs if m.get("dtv")}),
        "remitos": sorted({m["remito"] for m in movs if m.get("remito")}),
    }
