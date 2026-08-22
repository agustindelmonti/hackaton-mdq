"""
core/cerebro.py — TODO lo que el sistema sabe, y cómo se cruza.

EL MAPA Y EL CEREBRO NO SON LA MISMA VISTA, Y LA DIFERENCIA IMPORTA.

El mapa (core/mapa.py) tiene tres capas fijas y responde una pregunta cerrada:
de dónde viene, dónde está y adónde va cada kilo. La posición significa algo y
por eso se explica sola. Es la vista para decidir.

El cerebro es lo de abajo: las CIENTO OCHENTA entidades individuales —cada
lote, cada variedad, cada categoría del INASE, cada campo, cada cámara, cada
cliente— y las relaciones reales que las unen. Al correr el layout de fuerzas
las entidades muy conectadas migran solas al centro, y ese núcleo denso ES el
negocio. Es la vista para explorar y para contestar «¿qué más toca esto?».

ACÁ NO SE INFIERE NADA.

En un almacén el puente cliente↔producto había que deducirlo del rubro del
comercio. Acá no hace falta: la trazabilidad de semilla fiscalizada obliga a
que cada lote declare su variedad, su categoría, su campaña, su campo de origen
y dónde está. Todas las aristas de este grafo son CAMPOS DECLARADOS del lote o
renglones de una orden de carga. Si alguien pregunta «¿esto lo inventaron?», la
respuesta es abrir el JSON del lote y leer el campo.

Lo único propio es el TAMAÑO del punto (kilos del nodo) y eso no es un número
de negocio: es escala visual, y va declarado en `meta.derivados`.
"""
from __future__ import annotations

from . import conciliacion, movimientos, ordenes_carga, semilla, store
from .fechas import hoy, parse_fecha

# Cuánto de la ventana de brotación se considera "corriendo contra el reloj".
# El mismo número que usa el mapa y las oportunidades: uno solo en el sistema.
from .mapa import VENTANA_BROTACION_DIAS

# Los colores no se eligen en la pantalla: cada TIPO de entidad tiene el suyo y
# es el mismo en el grafo, en la leyenda y en el panel.
TIPOS = {
    "lote": "#2b7a8c",
    "variedad": "#2f7d5b",
    "categoria": "#6b4f9e",
    "campo": "#8a6d3b",
    "campania": "#9a9287",
    "ubicacion": "#1e2f6f",
    "orden": "#b8860b",
    "cliente": "#c05621",
    "pais": "#4a4a4a",
}


def _nodo(nid, tipo, etiqueta, **extra) -> dict:
    return {"id": nid, "tipo": tipo, "etiqueta": etiqueta, **extra}


def completo() -> dict:
    arts = [a for a in store.raw_actual() if float(a.get("stock") or 0) != 0]
    h = hoy()

    nodos: dict[str, dict] = {}
    aristas: list[dict] = []

    def asegurar(nid, tipo, etiqueta, **extra):
        if nid not in nodos:
            nodos[nid] = _nodo(nid, tipo, etiqueta, kg=0.0, lotes=0, **extra)
        return nodos[nid]

    def unir(a, b, rel):
        aristas.append({"id": f"{a}|{b}|{rel}", "origen": a, "destino": b, "rel": rel})

    # --- las ubicaciones, que son el centro de todo -------------------------
    for u in conciliacion.por_ubicacion():
        n = asegurar(f"ubi:{u['id']}", "ubicacion", u["nombre"],
                     estado=u["estado"], detalle=u.get("direccion"),
                     metricas={"toneladas": u["toneladas"], "lotes": u["lotes"],
                               "ocupacion_pct": u["ocupacion_pct"],
                               "diferencias": u["diferencias_abiertas"]})
        # Los kilos de la ubicación se cargan acá y no sumando lote por lote:
        # sin esto las cuatro cámaras quedaban del tamaño de un lote suelto y el
        # grafo perdía sus cuatro anclas — que es justamente lo que hay que ver.
        n["kg"] = float(u["toneladas"]) * 1000

    # --- el catálogo del rubro ---------------------------------------------
    dorm = {v["nombre"]: v for v in semilla.variedades()}
    campos_cat = {c["nombre"]: c for c in semilla.campos()}

    # --- cada lote, con todo lo que declara --------------------------------
    difs_por_lote = {d.get("lote") for d in conciliacion.abiertas()}
    for a in arts:
        kg = float(a.get("stock") or 0)
        lote = a.get("lote") or str(a.get("codigo"))
        nid = f"lote:{lote}"
        b = parse_fecha(a.get("brotacion_estimada"))
        dias = (b - h).days if b else None
        estado = "neutro"
        if lote in difs_por_lote:
            estado = "rojo"
        elif dias is not None and dias <= 0:
            estado = "rojo"
        elif dias is not None and dias <= VENTANA_BROTACION_DIAS:
            estado = "amarillo"
        nodos[nid] = _nodo(
            nid, "lote", lote, kg=kg, lotes=1, estado=estado,
            detalle=a.get("descripcion"),
            metricas={
                "kilos": round(kg, 1),
                "bolsones": round(kg / 1000, 1),
                "valor": round(kg * float(a.get("costo_iva") or 0), 2),
                "dias_hasta_brotacion": dias,
                "virus_pct": a.get("virus_pct"),
                "calibre": (f"{a.get('cota_inf')}–{a.get('cota_sup')} mm"
                            if a.get("cota_inf") else None),
                "analisis": a.get("analisis_estado"),
            },
        )

        # las cinco relaciones que la trazabilidad OBLIGA a declarar
        for campo, tipo, prefijo in (
            ("variedad", "variedad", "var"),
            ("categoria_semilla", "categoria", "cat"),
            ("campo_origen", "campo", "campo"),
            ("campania", "campania", "camp"),
        ):
            v = a.get(campo)
            if not v:
                continue
            oid = f"{prefijo}:{v}"
            extra = {}
            if tipo == "variedad":
                extra = {"detalle": (dorm.get(v) or {}).get("destino"),
                         "metricas": {"dormancia_dias": (dorm.get(v) or {}).get("dormancia_dias")}}
            if tipo == "campo":
                m = campos_cat.get(v) or {}
                extra = {"detalle": m.get("zona"),
                         "metricas": {"hectareas": m.get("ha"), "rinde": m.get("rinde")}}
            o = asegurar(oid, tipo, str(v), **extra)
            o["kg"] += kg
            o["lotes"] += 1
            unir(nid, oid, campo)

        if a.get("ubicacion_id"):
            unir(nid, f"ubi:{a['ubicacion_id']}", "esta_en")

    # --- lo comprometido: órdenes, clientes, países -------------------------
    cat_cli = {c["id"]: c for c in semilla.clientes()}
    for o in ordenes_carga.pendientes_con_estado():
        oid = f"orden:{o['numero']}"
        bloqueada = not o.get("puede_emitirse")
        asegurar(oid, "orden", o["numero"],
                 estado="rojo" if bloqueada else "verde",
                 detalle=o.get("cliente"),
                 metricas={"kilos": o.get("kg_total"), "bultos": o.get("bolsones_total"),
                           "bloqueos": len(o.get("bloqueos") or [])})
        nodos[oid]["kg"] = float(o.get("kg_total") or 0)
        for it in o.get("items") or []:
            if it.get("lote") and f"lote:{it['lote']}" in nodos:
                unir(f"lote:{it['lote']}", oid, "comprometido")
        cid = o.get("cliente_id") or o.get("cliente")
        if cid:
            meta = cat_cli.get(cid, {})
            c = asegurar(f"cli:{cid}", "cliente", o.get("cliente") or str(cid),
                         detalle=o.get("pais"),
                         metricas={"incoterm": meta.get("incoterm"),
                                   "puerto": meta.get("puerto")})
            c["kg"] += float(o.get("kg_total") or 0)
            c["lotes"] += 1
            unir(oid, f"cli:{cid}", "para")
            if o.get("pais"):
                p = asegurar(f"pais:{o['pais']}", "pais", o["pais"])
                p["kg"] += float(o.get("kg_total") or 0)
                unir(f"cli:{cid}", f"pais:{o['pais']}", "destino")

    # --- lo que se movió entre cámaras -------------------------------------
    nombre_a_id = {u["nombre"]: u["id"] for u in semilla.ubicaciones()}
    flujos: dict[tuple, dict] = {}
    for m in movimientos.listar():
        a_, b_ = nombre_a_id.get(m.get("origen")), nombre_a_id.get(m.get("destino"))
        if not a_ or not b_ or a_ == b_:
            continue
        k = tuple(sorted((a_, b_)))
        g = flujos.setdefault(k, {"n": 0, "kg": 0.0})
        g["n"] += 1
        g["kg"] += float(m.get("kg") or 0)
    for (a_, b_), g in flujos.items():
        aristas.append({"id": f"ubi:{a_}|ubi:{b_}|traslado", "origen": f"ubi:{a_}",
                        "destino": f"ubi:{b_}", "rel": "traslado",
                        "kg": round(g["kg"], 1), "n": g["n"], "fuerte": True})

    lista = list(nodos.values())
    for n in lista:
        n["kg"] = round(n["kg"], 1)

    conteo = {}
    for n in lista:
        conteo[n["tipo"]] = conteo.get(n["tipo"], 0) + 1

    return {
        "nodos": lista,
        "aristas": aristas,
        "tipos": [{"id": k, "color": v, "n": conteo.get(k, 0)} for k, v in TIPOS.items()],
        "resumen": {
            "nodos": len(lista), "aristas": len(aristas),
            "por_tipo": conteo,
            "movimientos": len(movimientos.listar()),
        },
        "meta": {
            "derivados": [
                "El TAMAÑO de cada punto es la suma de kilos de esa entidad. "
                "Es escala visual, no un número de negocio.",
            ],
            "fuente": ("Todas las líneas son campos DECLARADOS del lote (variedad, "
                       "categoría, campaña, campo de origen, ubicación) o renglones "
                       "de una orden de carga. Acá no se infiere ninguna relación."),
        },
    }
