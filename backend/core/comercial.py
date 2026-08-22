"""
comercial.py · «Che, ¿cuánto le vendimos a este cliente?»

Es la otra pregunta que hacen seguido, y hoy la contestan **remito por remito**.

Lo pidieron con una precisión que conviene respetar al pie de la letra:

    «Queremos poder verla en forma desagregada, camión por camión. Ahora,
     cuando necesitemos un resumen…»

Las dos vistas, no una. Por eso acá el dato nace **por remito** —que es el
camión— y el resumen se arma sumando remitos, nunca al revés. Así el total
siempre se puede abrir y llegar a la fila del Excel.

UN REMITO TIENE VARIAS FILAS. El camión es la unidad, el lote es el detalle: el
remito 807 llevó lote 224 y lote 223. Cuando alguien mira un remito ve el camión
arriba y los lotes que llevó abajo; cuando mira un lote, puede subir al remito y
al camión. Aplanar eso en una fila por lote sería perder el camión, que es
justamente lo que quieren ver.
"""
from __future__ import annotations

from collections import defaultdict

from . import papasud_real as real
from .fechas import hoy


def _entregas() -> list[dict]:
    return [m for m in real.movimientos() if m.get("tipo") == "entrega_cliente"]


def clientes() -> list[dict]:
    """Todos los clientes con lo que se les entregó. Ordenado por kilos."""
    g: dict[str, dict] = {}
    for m in _entregas():
        d = m.get("destino") or {}
        cid = d.get("id")
        if not cid:
            continue
        c = g.setdefault(cid, {"id": cid, "nombre": cid.title(), "kg": 0,
                               "bolsas": 0, "remitos": set(), "variedades": set(),
                               "primera": None, "ultima": None})
        c["kg"] += m.get("kg") or 0
        c["bolsas"] += m.get("bolsas") or 0
        c["remitos"].add(m.get("remito"))
        if m.get("variedad"):
            c["variedades"].add(m["variedad"])
        f = m.get("fecha")
        if f:
            c["primera"] = min(c["primera"] or f, f)
            c["ultima"] = max(c["ultima"] or f, f)
    out = []
    for c in g.values():
        c["camiones"] = len(c["remitos"])
        c["remitos"] = sorted(x for x in c["remitos"] if x)
        c["variedades"] = sorted(c["variedades"])
        out.append(c)
    return sorted(out, key=lambda c: -c["kg"])


def ventas(*, cliente: str | None = None, desde: str | None = None,
           hasta: str | None = None, variedad: str | None = None) -> dict:
    """Lo entregado, en las dos vistas: el resumen y el camión por camión."""
    filas = []
    for m in _entregas():
        d = m.get("destino") or {}
        if cliente and d.get("id") != cliente:
            continue
        if variedad and m.get("variedad") != variedad:
            continue
        f = m.get("fecha") or ""
        if desde and f < desde:
            continue
        if hasta and f > hasta:
            continue
        filas.append(m)

    def cortar(clave):
        g: dict = {}
        for m in filas:
            k = clave(m) or "sin declarar"
            x = g.setdefault(k, {"clave": k, "kg": 0, "bolsas": 0, "camiones": set()})
            x["kg"] += m.get("kg") or 0
            x["bolsas"] += m.get("bolsas") or 0
            x["camiones"].add(m.get("remito"))
        for x in g.values():
            x["camiones"] = len(x["camiones"])
        return sorted(g.values(), key=lambda x: -x["kg"])

    return {
        "filtro": {"cliente": cliente, "desde": desde, "hasta": hasta,
                   "variedad": variedad},
        "kg": sum(m.get("kg") or 0 for m in filas),
        "bolsas": sum(m.get("bolsas") or 0 for m in filas),
        "camiones": len({m.get("remito") for m in filas}),
        "por_variedad": cortar(lambda m: m.get("variedad")),
        "por_calibre": cortar(lambda m: m.get("calibre")),
        "por_categoria": cortar(lambda m: m.get("categoria")),
        "por_lote": cortar(lambda m: m.get("lote")),
        "por_mes": sorted(cortar(lambda m: (m.get("fecha") or "")[:7]),
                          key=lambda x: x["clave"]),
        "por_cliente": cortar(lambda m: (m.get("destino") or {}).get("id")),
        "camion_por_camion": remitos(filas),
    }


def remitos(filas: list[dict]) -> list[dict]:
    """El camión arriba, los lotes que llevó abajo. Nunca al revés."""
    g: dict[str, dict] = {}
    for m in filas:
        rid = m.get("remito_id") or f"{m.get('tipo')}:{m.get('remito')}"
        r = g.setdefault(rid, {
            "remito_id": rid, "remito": m.get("remito"), "fecha": m.get("fecha"),
            "transporte": m.get("transporte"), "chofer": m.get("chofer"),
            "cliente": (m.get("destino") or {}).get("id"),
            "origen": real.nombre_nodo(m.get("origen")),
            "kg": 0, "bolsas": 0, "dtvs": [], "lineas": [], "anomalias": [],
        })
        r["kg"] += m.get("kg") or 0
        r["bolsas"] += m.get("bolsas") or 0
        if m.get("dtv") and m["dtv"] not in r["dtvs"]:
            r["dtvs"].append(m["dtv"])
        for a in m.get("anomalias") or []:
            if a not in r["anomalias"]:
                r["anomalias"].append(a)
        r["lineas"].append({
            "lote": m.get("lote"), "variedad": m.get("variedad"),
            "categoria": m.get("categoria"), "calibre": m.get("calibre"),
            "kg": m.get("kg"), "bolsas": m.get("bolsas"),
            "kg_prom": m.get("kg_prom"), "dtv": m.get("dtv"),
            "bolsa_color": m.get("bolsa_color"), "hilo_color": m.get("hilo_color"),
            "observaciones": m.get("observaciones"),
            "fuente": m.get("fuente"), "anomalias": m.get("anomalias") or [],
            "movimiento": m.get("id"),
        })
    for r in g.values():
        r["lotes"] = len(r["lineas"])
    return sorted(g.values(), key=lambda r: (r["fecha"] or "", r["remito"] or ""),
                  reverse=True)


def comparar(*, meses: int = 12) -> dict:
    """Cliente contra cliente, y este período contra el anterior."""
    fin = hoy().isoformat()
    corte = f"{hoy().year - 1}-{hoy().month:02d}-01"
    actual = {c["clave"]: c for c in ventas(desde=corte, hasta=fin)["por_cliente"]}
    previo = {c["clave"]: c for c in ventas(hasta=corte)["por_cliente"]}
    filas = []
    for cid in set(actual) | set(previo):
        a = actual.get(cid, {}).get("kg", 0)
        p = previo.get(cid, {}).get("kg", 0)
        filas.append({
            "cliente": cid, "nombre": cid.title(),
            "kg": a, "kg_anterior": p, "delta": a - p,
            "variacion": None if not p else round((a - p) / p * 100, 1),
            "camiones": actual.get(cid, {}).get("camiones", 0),
            "nuevo": p == 0 and a > 0,
            "perdido": a == 0 and p > 0,
        })
    return {"desde": corte, "hasta": fin, "meses": meses,
            "clientes": sorted(filas, key=lambda f: -f["kg"])}


def transportistas(*, desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Kilos movidos por transportista — lo que administración usa para pagar.

    «Esta misma planilla la usa la administración: hay que pagarle al camión A,
     bueno, camión A, ¿cuántos kilos trajo? Listo, acá está la información.»

    Sale del mismo libro, sin volver a cargar nada. Los kilos por transportista
    son los mismos que los del stock: es un solo dato mirado de dos maneras.
    """
    g: dict[str, dict] = defaultdict(lambda: {
        "kg": 0, "viajes": set(), "choferes": set(), "tipos": defaultdict(int)})
    for m in real.movimientos():
        t = m.get("transporte")
        if not t:
            continue
        f = m.get("fecha") or ""
        if (desde and f < desde) or (hasta and f > hasta):
            continue
        d = g[t]
        d["kg"] += m.get("kg") or 0
        d["viajes"].add(m.get("remito_id") or m.get("id"))
        if m.get("chofer"):
            d["choferes"].add(m["chofer"])
        d["tipos"][m.get("tipo")] += m.get("kg") or 0
    return sorted(
        [{"transporte": t, "nombre": t.title(), "kg": d["kg"],
          "viajes": len(d["viajes"]), "choferes": sorted(d["choferes"]),
          "por_tipo": dict(d["tipos"])} for t, d in g.items()],
        key=lambda x: -x["kg"])


def frigorificos(*, desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Kilos que entraron y salieron de cada frigorífico subcontratado.

    «Los depósitos son subcontratados, tampoco son nuestros. Hay que traquear
     todos los movimientos por lugar porque se tienen que pagar los servicios.»
    """
    g: dict[str, dict] = defaultdict(
        lambda: {"entrada_kg": 0, "salida_kg": 0, "movimientos": 0})
    for m in real.movimientos():
        f = m.get("fecha") or ""
        if (desde and f < desde) or (hasta and f > hasta):
            continue
        for lado, campo in (("destino", "entrada_kg"), ("origen", "salida_kg")):
            n = m.get(lado) or {}
            if n.get("tipo") == "frigorifico":
                g[n["id"]][campo] += m.get("kg") or 0
                g[n["id"]]["movimientos"] += 1
    # El saldo NO es la resta cruda: sale del libro de partidas, que separa lo
    # que entró antes de que empezara esta planilla. Un frigorífico del que se
    # retiró más de lo que esta planilla registra que entró no tiene stock
    # negativo — tiene stock viejo que la planilla no cuenta.
    from . import disponibilidad
    out = []
    for u, d in g.items():
        ps = disponibilidad.partidas(ubicacion=u)
        anterior = sum(s["kg"] for s in disponibilidad.libro()["saldos_anteriores"]
                       if s["ubicacion"] == u)
        out.append({
            "ubicacion": u, "nombre": real.nombre_ubicacion(u), **d,
            "stock_kg": round(sum(p["kg"] for p in ps)),
            "saldo_anterior_kg": round(anterior),
            "descuadre": round(d["salida_kg"] - d["entrada_kg"]),
        })
    return sorted(out, key=lambda x: -x["entrada_kg"])
