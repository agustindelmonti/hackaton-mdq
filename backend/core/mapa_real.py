"""
mapa_real.py · El mapa del flujo REAL de Papasud.

El mapa viejo (`core.mapa`) pinta cuatro depósitos en un cuadro. Eso era el
modelo de inventario de antes de hablar con Papasud. El flujo real, textual
de Leandro y Sergio el 22/08:

    lote (campo) → PLANTA (recepción / reclasificación / playa)
                      ├→ cliente
                      ├→ frigorífico → vuelve a planta → cliente
                      └→ frigorífico → cliente (poco común)
    atajos: campo → frío, campo → cliente

La PLANTA es el hub. Los frigoríficos son almacenamiento subcontratado, no
el mostrador. Cada lote de un campo es UNA variedad — si el mapa los mezcla,
está mintiendo.

Números: salen de `stock_real` (vista derivada del libro). El LLM no calcula.
Los ids se sanean igual que en `core.mapa` (los `:` rompen React Flow).
"""
from __future__ import annotations

from collections import defaultdict

from . import modelo_real as M
from . import stock_real as S
from . import paths


def _sid(x: str) -> str:
    return x.replace(":", "_").replace(">", "_").replace(" ", "_")


def _nodo(nid, tipo, capa, etiqueta, **extra) -> dict:
    return {"id": _sid(nid), "tipo": tipo, "capa": capa, "etiqueta": etiqueta, **extra}


def _arista(origen, destino, tipo, **extra) -> dict:
    o, d = _sid(origen), _sid(destino)
    return {"id": f"{o}__{d}__{tipo}", "origen": o, "destino": d, "tipo": tipo, **extra}


def _por_variedad_lotes(lotes: list[dict], kg_por_lote: dict[str, float] | None = None) -> list[dict]:
    por: dict[str, dict] = {}
    for l in lotes:
        g = por.setdefault(l["variedad_id"], {
            "variedad_id": l["variedad_id"], "variedad": l["variedad"],
            "lotes": [], "kg": 0.0,
        })
        g["lotes"].append(l["id"])
        if kg_por_lote is not None:
            g["kg"] += kg_por_lote.get(l["id"], 0.0)
        else:
            g["kg"] += float(l.get("kg_cosechado") or 0)
    return sorted(
        ({**g, "kg": round(g["kg"], 1), "n": len(g["lotes"])} for g in por.values()),
        key=lambda x: -x["kg"],
    )


def flujo() -> dict:
    """El grafo que Track C pinta: origen (lab + campos) → hub (planta) ⇄
    almacenamiento (frigoríficos) → destino (clientes)."""
    cat = M.catalogos()
    lotes = M.lotes()
    movs = M.movimientos()
    filas = S.stock_por_ubicacion()
    sitios = S.resumen_sitios()
    planta = cat["planta"]
    lab = cat.get("laboratorio") or {"id": "lab_invitro", "nombre": "Laboratorio in vitro"}

    stock_por_ubi: dict[str, list[dict]] = defaultdict(list)
    for f in filas:
        stock_por_ubi[f["ubicacion_id"]].append(f)

    nodos: list[dict] = []
    aristas: list[dict] = []

    # ----- ORIGEN: laboratorio + campos (con lotes agrupados por variedad) --
    n_lab = sum(1 for l in lotes if l.get("origen_laboratorio"))
    nodos.append(_nodo(
        lab["id"], "laboratorio", "origen", lab["nombre"],
        subtitulo="Meristemas · arranque de la escalera",
        metricas={"lotes": n_lab},
        detalle=lab.get("detalle"),
    ))

    kg_cosecha_campo: dict[str, float] = defaultdict(float)
    lotes_por_campo: dict[str, list[dict]] = defaultdict(list)
    for l in lotes:
        lotes_por_campo[l["campo_id"]].append(l)
        kg_cosecha_campo[l["campo_id"]] += float(l.get("kg_cosechado") or 0)

    for campo in cat["campos"]:
        xs = lotes_por_campo.get(campo["id"], [])
        stock_campo = stock_por_ubi.get(f"campo:{campo['id']}", [])
        kg_vivo = round(sum(f["kg"] for f in stock_campo), 1)
        nid = f"campo:{campo['id']}"
        nodos.append(_nodo(
            nid, "campo", "origen", campo["nombre"],
            subtitulo=campo.get("partido") or campo.get("provincia"),
            metricas={
                "lotes": len(xs),
                "kg_cosechado": round(kg_cosecha_campo[campo["id"]], 1),
                "kg": kg_vivo,
                "toneladas": round(kg_cosecha_campo[campo["id"]] / 1000, 1),
            },
            campo_id=campo["id"],
            partido=campo.get("partido"),
            provincia=campo.get("provincia"),
            alias=campo.get("alias") or [],
            grupos=_por_variedad_lotes(xs),
            detalle="Cada lote es una sola variedad. El 300 y el 101 no se mezclan.",
        ))
        if any(l.get("origen_laboratorio") for l in xs):
            aristas.append(_arista(lab["id"], nid, "multiplicacion",
                                   lotes=sum(1 for l in xs if l.get("origen_laboratorio"))))

    # ----- HUB: la planta, con las tres estaciones ---------------------------
    planta_stock = sitios.get("planta") or {
        "kg": 0.0, "lotes": 0, "bolsas": 0, "por_variedad": [],
    }
    detalle = S.detalle_planta()
    nodos.append(_nodo(
        planta["id"], "planta", "hub", planta["nombre"],
        subtitulo="Recepción · reclasificación · playa",
        metricas={
            "kg": planta_stock["kg"],
            "toneladas": round(planta_stock["kg"] / 1000, 1),
            "lotes": planta_stock["lotes"],
            "bolsas": planta_stock.get("bolsas") or 0,
        },
        tipo_sitio="planta",
        tiene_bascula=True,
        zonas=detalle["zonas"],
        flujos=detalle["flujos"],
        grupos=planta_stock.get("por_variedad") or [],
        detalle="El hub. La mercadería se hace en el campo, se recibe acá, y de acá sale.",
    ))

    # ----- ALMACENAMIENTO: frigoríficos subcontratados -----------------------
    frigo_por_id = {f["id"]: f for f in cat["frigorificos"]}
    for f in cat["frigorificos"]:
        uid = f"frigorifico:{f['id']}"
        xs = stock_por_ubi.get(uid, [])
        kg = round(sum(x["kg"] for x in xs), 1)
        nodos.append(_nodo(
            uid, "frigorifico", "almacenamiento", f["nombre"],
            subtitulo="Subcontratado · vuelve a planta",
            metricas={
                "kg": kg,
                "toneladas": round(kg / 1000, 1),
                "lotes": len({x["lote_id"] for x in xs}),
                "bolsas": round(sum(x["bolsas"] for x in xs)),
            },
            tipo_sitio="frigorifico",
            subcontratado=True,
            grupos=_agrupar_filas(xs),
        ))

    # ----- DESTINO: clientes -------------------------------------------------
    kg_cliente: dict[str, dict] = {}
    for m in movs:
        if m["tipo"] != "entrega_cliente":
            continue
        cid = m.get("cliente_id") or (m["destino_id"].split(":", 1)[1]
                                      if m["destino_id"].startswith("cliente:") else None)
        if not cid:
            continue
        g = kg_cliente.setdefault(cid, {"kg": 0.0, "n": 0, "desde": defaultdict(float)})
        g["kg"] += m["kg"]
        g["n"] += 1
        g["desde"][M.tipo_ubicacion(m["origen_id"])] += m["kg"]

    for c in cat["clientes"]:
        g = kg_cliente.get(c["id"], {"kg": 0.0, "n": 0, "desde": {}})
        nodos.append(_nodo(
            f"cliente:{c['id']}", "cliente", "destino", c["nombre"],
            metricas={"kg": round(g["kg"], 1), "entregas": g["n"],
                      "toneladas": round(g["kg"] / 1000, 1)},
            sale_desde={k: round(v, 1) for k, v in dict(g["desde"]).items()},
        ))

    # ----- ARISTAS: los movimientos reales, agregados por par de sitios ------
    flujos: dict[tuple[str, str, str], dict] = {}
    for m in movs:
        o, d, t = m["origen_id"], m["destino_id"], m["tipo"]
        if not o or not d or o == d:
            continue
        # el cliente es destino; el campo de origen de un ingreso_tolva es el campo
        k = (o, d, t)
        f = flujos.setdefault(k, {"kg": 0.0, "n": 0, "numeros": []})
        f["kg"] += m["kg"]
        f["n"] += 1
        f["numeros"].append(m["numero"])

    for (o, d, t), f in flujos.items():
        aristas.append(_arista(
            o, d, t,
            kg=round(f["kg"], 1),
            movimientos=f["n"],
            numeros=f["numeros"][:8],
            vehiculo="tolva" if t == "ingreso_tolva" else "camion_bolsas",
            principal=t in ("ingreso_tolva", "envio_frio", "retiro_frio", "entrega_cliente"),
        ))

    # La planta como marca del centro: el logo vive acá, no entre cuatro cámaras.
    nodos.append(_nodo(
        "marca:papasud", "marca", "hub", paths.EMPRESA,
        subtitulo="La planta es el hub · el frío es un desvío",
        logo=paths.LOGO,
        metricas={
            "toneladas": round((sitios.get("kg_total") or 0) / 1000, 1),
            "lotes": len({f["lote_id"] for f in filas if f["kg"] > 0}),
            "campos": len(cat["campos"]),
            "frigorificos": len(cat["frigorificos"]),
        },
    ))

    hallazgos = _hallazgos(nodos)

    ids = {n["id"] for n in nodos}
    aristas = [a for a in aristas if a["origen"] in ids and a["destino"] in ids]

    return {
        "modelo": "real",
        "regla": (
            "Un lote, una variedad. Campo → planta (báscula, reclasificación, playa) "
            "→ cliente o frío. El frío suele volver a planta. La venta sale de la planta."
        ),
        "capas": [
            {"id": "origen", "titulo": "De dónde sale",
             "detalle": "Laboratorio in vitro y campos. Cada lote es una variedad."},
            {"id": "hub", "titulo": "La planta",
             "detalle": "Recepción, reclasificación, playa. El centro de la mercadería."},
            {"id": "almacenamiento", "titulo": "Frigoríficos",
             "detalle": "Subcontratados. La mercadería suele volver a planta."},
            {"id": "destino", "titulo": "Adónde va",
             "detalle": "Cliente o exportación. Sale de la planta, no del frío."},
        ],
        "nodos": nodos,
        "aristas": aristas,
        "filas": filas,
        "hallazgos": hallazgos,
        "resumen": {
            "kg_en_planta": (sitios.get("planta") or {}).get("kg") or 0.0,
            "kg_en_frio": round(sum(s["kg"] for s in sitios.get("frigorificos") or []), 1),
            "kg_total": sitios.get("kg_total") or 0.0,
            "toneladas": round((sitios.get("kg_total") or 0) / 1000, 1),
            "lotes": len(lotes),
            "campos": len(cat["campos"]),
            "frigorificos": len(frigo_por_id),
            "recepciones": len(M.recepciones()),
            "ordenes_carga": len(M.ordenes_carga()),
            "reclasificaciones": len(M.reclasificaciones()),
        },
    }


def _agrupar_filas(xs: list[dict]) -> list[dict]:
    por: dict[str, dict] = {}
    for f in xs:
        g = por.setdefault(f["variedad_id"], {
            "variedad_id": f["variedad_id"], "variedad": f["variedad"],
            "kg": 0.0, "lotes": [],
        })
        g["kg"] += f["kg"]
        g["lotes"].append(f["lote_id"])
    return sorted(
        ({**g, "kg": round(g["kg"], 1), "n": len(g["lotes"])} for g in por.values()),
        key=lambda x: -x["kg"],
    )


def _hallazgos(nodos: list[dict]) -> list[dict]:
    """Caminos para iluminar: el circuito planta⇄frío, el atajo campo→cliente,
    y el lote 300 en Cayetano Chávez (el ejemplo que ellos dieron)."""
    ids = {n["id"] for n in nodos}
    out = []

    def _ok(camino: list[str]) -> list[str]:
        return [c for c in camino if c in ids]

    planta = _sid(M.catalogos()["planta"]["id"])
    out.append({
        "id": "circuito_frio",
        "clase": "circuito",
        "titulo": "El circuito más común: planta → frío → planta → cliente",
        "detalle": "No sale del frigorífico a la venta. Vuelve a planta y despacha de ahí.",
        "camino": {"nodos": _ok([planta] + [_sid(f"frigorifico:{f['id']}")
                                            for f in M.catalogos()["frigorificos"]][:2]),
                   "aristas": []},
        "seccion": "mapa",
    })
    lote_300 = M.lote("300")
    if lote_300:
        campo_n = _sid(f"campo:{lote_300['campo_id']}")
        out.append({
            "id": "lote_300",
            "clase": "linaje",
            "titulo": f"Lote 300 · {lote_300['variedad']} en {lote_300['campo']}",
            "detalle": (
                f"Un lote, una variedad. El 300 es {lote_300['variedad']}, no se mezcla "
                f"con el de al lado. Campo {lote_300['campo']} → planta."
            ),
            "camino": {"nodos": _ok([campo_n, planta]), "aristas": []},
            "seccion": "mapa",
        })
    return out
