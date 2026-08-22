"""
liquidacion.py · Cuánto y cuándo hay que pagarle a cada transportista y a cada
frigorífico (PLAN_TRACKS_PAPASUD.md, Track B §5).

Textual de Papasud: "hay que pagarle al camión A, ¿cuántos kilos trajo? Listo,
acá está la información. No tenemos que andar buscando remito por remito."

Esto no está en ninguna vertical del brief — es media empresa, y lo
resolvemos con el mismo libro de movimientos que ya sostiene el stock.
"""
from __future__ import annotations

import datetime

from . import modelo_real as M


def _en_rango(fecha: str, desde: str | None, hasta: str | None) -> bool:
    if desde and fecha < desde:
        return False
    if hasta and fecha > hasta:
        return False
    return True


def liquidacion_transportistas(desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Kg movidos y flete a pagar por transportista, en el período pedido."""
    catalogo = {t["id"]: t["nombre"] for t in M.catalogos()["transportistas"]}
    acumulado: dict[str, dict] = {}

    for m in M.movimientos():
        tid = m.get("transportista_id")
        if not tid or not _en_rango(m["fecha"], desde, hasta):
            continue
        acc = acumulado.setdefault(tid, {
            "transportista_id": tid,
            "transportista": catalogo.get(tid, tid),
            "kg_movidos": 0.0,
            "viajes": 0,
            "a_pagar": 0.0,
            "movimientos": [],
        })
        acc["kg_movidos"] += m["kg"]
        acc["viajes"] += 1
        acc["a_pagar"] += m.get("valor_flete") or 0.0
        acc["movimientos"].append({
            "numero": m["numero"], "remito": m["remito"], "fecha": m["fecha"],
            "tipo": m["tipo"], "lote_id": m["lote_id"], "kg": m["kg"],
            "valor_flete": m.get("valor_flete"),
        })

    salida = []
    for acc in acumulado.values():
        acc["kg_movidos"] = round(acc["kg_movidos"], 1)
        acc["a_pagar"] = round(acc["a_pagar"], 2)
        acc["movimientos"].sort(key=lambda x: x["fecha"])
        salida.append(acc)
    return sorted(salida, key=lambda a: -a["a_pagar"])


def liquidacion_frigorificos(desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Kg movidos por frigorífico (subcontratado) en el período — la base para
    pagar el servicio de guarda."""
    catalogo = {f["id"]: f["nombre"] for f in M.catalogos()["frigorificos"]}
    acumulado: dict[str, dict] = {}

    for m in M.movimientos():
        for lado, ubic_id in (("origen", m["origen_id"]), ("destino", m["destino_id"])):
            if not ubic_id.startswith("frigorifico:"):
                continue
            if not _en_rango(m["fecha"], desde, hasta):
                continue
            fid = ubic_id.split(":", 1)[1]
            acc = acumulado.setdefault(fid, {
                "frigorifico_id": fid,
                "frigorifico": catalogo.get(fid, fid),
                "kg_ingresados": 0.0,
                "kg_retirados": 0.0,
                "movimientos": [],
            })
            if lado == "destino" and m["tipo"] == "envio_frio":
                acc["kg_ingresados"] += m["kg"]
            elif lado == "origen" and m["tipo"] == "retiro_frio":
                acc["kg_retirados"] += m["kg"]
            acc["movimientos"].append({
                "numero": m["numero"], "remito": m["remito"], "fecha": m["fecha"],
                "tipo": m["tipo"], "lote_id": m["lote_id"], "kg": m["kg"],
            })

    salida = []
    for acc in acumulado.values():
        acc["kg_ingresados"] = round(acc["kg_ingresados"], 1)
        acc["kg_retirados"] = round(acc["kg_retirados"], 1)
        acc["movimientos"].sort(key=lambda x: x["fecha"])
        salida.append(acc)
    return sorted(salida, key=lambda a: -a["kg_ingresados"])
