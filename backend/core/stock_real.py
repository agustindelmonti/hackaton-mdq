"""
stock_real.py · Stock como VISTA derivada del libro de movimientos + el motor
determinista de "bloqueo con alternativa".

Regla de arquitectura #1: el LLM nunca calcula. Todo lo de acá es Python
plano. Ángela (Track A) sólo tiene que llamar a `verificar_pedido` y narrar
el resultado — nunca inventar un lote alternativo por su cuenta.

Regla de arquitectura #2: el stock NUNCA es una celda editable. Es la suma
del libro de movimientos (`modelo_real.movimientos()`), calculada acá.
"""
from __future__ import annotations

from . import modelo_real as M


def stock_por_lote_ubicacion() -> dict[tuple[str, str], float]:
    """La vista derivada: kg netos por (lote_id, ubicacion_id). Sólo cuenta lo
    CONFIRMADO en destino — lo en_transito no está en ningún lado todavía."""
    saldo: dict[tuple[str, str], float] = {}
    for m in M.movimientos():
        lote_id, origen, destino, kg = m["lote_id"], m["origen_id"], m["destino_id"], m["kg"]
        saldo[(lote_id, origen)] = saldo.get((lote_id, origen), 0.0) - kg
        if m["tipo"] != "entrega_cliente" and m.get("confirmado_en_destino", True):
            saldo[(lote_id, destino)] = saldo.get((lote_id, destino), 0.0) + kg
    return saldo


def stock_por_ubicacion(min_kg: float = 0.5) -> list[dict]:
    """Una fila por (lote, ubicación) con stock vivo — la base del mapa y de
    las consultas de disponibilidad."""
    saldo = stock_por_lote_ubicacion()
    filas = []
    for (lote_id, ubic_id), kg in saldo.items():
        if kg < min_kg:
            continue
        l = M.lote(lote_id)
        if not l:
            continue
        filas.append({
            "lote_id": lote_id,
            "variedad_id": l["variedad_id"],
            "variedad": l["variedad"],
            "categoria_id": l["categoria_id"],
            "categoria": l["categoria"],
            "calibre_id": l["calibre_id"],
            "calibre": l["calibre"],
            "ubicacion_id": ubic_id,
            "ubicacion": M.nombre_ubicacion(ubic_id),
            "kg": round(kg, 1),
            "bolsas": round(kg / l["kg_por_bolsa"]),
        })
    return filas


def disponibilidad_por_variedad(variedad_id: str, calibre_id: str | None = None) -> list[dict]:
    filas = [f for f in stock_por_ubicacion() if f["variedad_id"] == variedad_id]
    if calibre_id:
        filas = [f for f in filas if f["calibre_id"] == calibre_id]
    return sorted(filas, key=lambda f: -f["kg"])


def resumen_variedad(variedad_id: str) -> dict:
    filas = disponibilidad_por_variedad(variedad_id)
    total_kg = sum(f["kg"] for f in filas)
    por_ubicacion: dict[str, float] = {}
    for f in filas:
        por_ubicacion[f["ubicacion"]] = por_ubicacion.get(f["ubicacion"], 0.0) + f["kg"]
    return {
        "variedad_id": variedad_id,
        "kg_total": round(total_kg, 1),
        "bolsas_total": round(sum(f["bolsas"] for f in filas)),
        "por_ubicacion": [{"ubicacion": u, "kg": round(kg, 1)} for u, kg in por_ubicacion.items()],
        "lotes": filas,
    }


def _agrupar_variedades(filas: list[dict]) -> list[dict]:
    por: dict[str, dict] = {}
    for f in filas:
        g = por.setdefault(f["variedad_id"], {
            "variedad_id": f["variedad_id"], "variedad": f["variedad"],
            "kg": 0.0, "bolsas": 0, "lotes": 0,
        })
        g["kg"] += f["kg"]
        g["bolsas"] += f["bolsas"]
        g["lotes"] += 1
    return sorted(
        ({**g, "kg": round(g["kg"], 1)} for g in por.values()),
        key=lambda x: -x["kg"],
    )


def resumen_sitios() -> dict:
    """Una fila por sitio vivo (planta, cada frigorífico, cada campo con
    remanente). Es lo que el mapa pinta en grande: 'esta planta tiene tantos
    kilos, este frío tiene tantos, este lote tiene tantos'."""
    filas = stock_por_ubicacion()
    por_ubi: dict[str, list[dict]] = {}
    for f in filas:
        por_ubi.setdefault(f["ubicacion_id"], []).append(f)

    def _sitio(ubic_id: str, xs: list[dict]) -> dict:
        return {
            "ubicacion_id": ubic_id,
            "ubicacion": M.nombre_ubicacion(ubic_id),
            "tipo": M.tipo_ubicacion(ubic_id),
            "kg": round(sum(x["kg"] for x in xs), 1),
            "bolsas": round(sum(x["bolsas"] for x in xs)),
            "lotes": len({x["lote_id"] for x in xs}),
            "por_variedad": _agrupar_variedades(xs),
        }

    sitios = [_sitio(uid, xs) for uid, xs in por_ubi.items()]
    planta_id = M.catalogos()["planta"]["id"]
    return {
        "planta": next((s for s in sitios if s["ubicacion_id"] == planta_id), None),
        "frigorificos": sorted(
            [s for s in sitios if s["tipo"] == "frigorifico"], key=lambda s: -s["kg"]),
        "campos": sorted(
            [s for s in sitios if s["tipo"] == "campo"], key=lambda s: -s["kg"]),
        "kg_total": round(sum(s["kg"] for s in sitios if s["tipo"] in ("planta", "frigorifico")), 1),
        "sitios": sitios,
    }


def detalle_planta() -> dict:
    """La planta como hub: zonas, stock vivo, recepciones y reclasificaciones.
    Los números salen del libro; las zonas son estaciones de proceso, no
    depósitos separados (el stock vive en planta_mdp)."""
    cat = M.catalogos()
    planta = cat["planta"]
    filas = [f for f in stock_por_ubicacion() if f["ubicacion_id"] == planta["id"]]
    recs = M.recepciones()
    rcls = M.reclasificaciones()
    ocs = M.ordenes_carga()
    movs = [m for m in M.movimientos()
            if m["origen_id"] == planta["id"] or m["destino_id"] == planta["id"]]

    def _kg_tipo(tipo: str, lado: str) -> float:
        return round(sum(m["kg"] for m in movs if m["tipo"] == tipo
                         and m[lado] == planta["id"]), 1)

    zonas = []
    for z in planta.get("zonas") or cat.get("zonas_planta") or []:
        if z["id"] == "recepcion":
            extra = {
                "recepciones": len(recs),
                "kg_ingresados": round(sum(r["peso_bascula_kg"] or 0 for r in recs), 1),
                "ordenes_sin_remito": sum(1 for r in recs if r.get("sin_remito_de_origen")),
            }
        elif z["id"] == "reclasificacion":
            extra = {
                "reclasificaciones": len(rcls),
                "kg_embolsados": round(sum(r["kg_embolsado"] for r in rcls), 1),
                "bolsas": round(sum(r["bolsas"] for r in rcls)),
            }
        else:
            extra = {
                "kg_envio_frio": _kg_tipo("envio_frio", "origen_id"),
                "kg_retiro_frio": _kg_tipo("retiro_frio", "destino_id"),
                "kg_entrega_cliente": _kg_tipo("entrega_cliente", "origen_id"),
            }
        zonas.append({**z, **extra})

    return {
        "planta": planta,
        "kg": round(sum(f["kg"] for f in filas), 1),
        "bolsas": round(sum(f["bolsas"] for f in filas)),
        "lotes": len({f["lote_id"] for f in filas}),
        "por_variedad": _agrupar_variedades(filas),
        "zonas": zonas,
        "flujos": {
            "ingreso_tolva_kg": _kg_tipo("ingreso_tolva", "destino_id"),
            "envio_frio_kg": _kg_tipo("envio_frio", "origen_id"),
            "retiro_frio_kg": _kg_tipo("retiro_frio", "destino_id"),
            "entrega_cliente_kg": _kg_tipo("entrega_cliente", "origen_id"),
        },
        "recepciones_recientes": sorted(recs, key=lambda r: r["fecha"], reverse=True)[:12],
        "ordenes_en_papel": sum(1 for o in ocs if o.get("canal") == "papel"),
        "stock": filas,
    }


# ----------------------------------------------------------------------------
# El motor de bloqueo con alternativa. Ver PLAN_TRACKS_PAPASUD.md §2:
# "no alcanza con frenar, hay que frenar y RESOLVER". Es pura función
# determinista — nada de LLM adentro.
# ----------------------------------------------------------------------------
def verificar_pedido(
    variedad_id: str,
    kg_pedido: float,
    lote_id: str | None = None,
    ubicacion_id: str | None = None,
    calibre_requerido: str | None = None,
) -> dict:
    """Verifica si un pedido puede emitirse contra el lote/ubicación pedidos.

    Si no alcanza, busca alternativas: otros lotes de la MISMA variedad, con
    calibre compatible si se pidió uno, ordenados por stock disponible.
    Si un solo lote no alcanza, también evalúa combinaciones de a dos.
    """
    filas = disponibilidad_por_variedad(variedad_id)

    objetivo = None
    if lote_id:
        objetivo = next((f for f in filas if f["lote_id"] == lote_id
                          and (ubicacion_id is None or f["ubicacion_id"] == ubicacion_id)), None)
    kg_en_objetivo = objetivo["kg"] if objetivo else 0.0

    if objetivo and kg_en_objetivo >= kg_pedido:
        return {
            "bloqueado": False,
            "variedad_id": variedad_id,
            "kg_pedido": kg_pedido,
            "lote_id": lote_id,
            "ubicacion_id": objetivo["ubicacion_id"],
            "kg_disponible": kg_en_objetivo,
            "mensaje": (
                f"Hay stock suficiente: {kg_en_objetivo:.0f} kg del lote {lote_id} "
                f"en {objetivo['ubicacion']}."
            ),
        }

    # No alcanza en el lote/ubicación pedidos. Buscamos alternativas: mismo
    # variedad, calibre compatible, excluyendo el lote/ubicación ya evaluados.
    candidatos = [
        f for f in filas
        if not (f["lote_id"] == lote_id and (ubicacion_id is None or f["ubicacion_id"] == ubicacion_id))
        and (calibre_requerido is None or f["calibre_id"] == calibre_requerido)
    ]
    candidatos.sort(key=lambda f: -f["kg"])

    faltante = round(kg_pedido - kg_en_objetivo, 1)
    alternativa_simple = next((f for f in candidatos if f["kg"] >= kg_pedido), None)

    combinacion = None
    if not alternativa_simple:
        acumulado = 0.0
        elegidos: list[dict] = []
        for f in candidatos:
            elegidos.append(f)
            acumulado += f["kg"]
            if acumulado >= kg_pedido:
                combinacion = elegidos
                break

    resultado = {
        "bloqueado": True,
        "variedad_id": variedad_id,
        "kg_pedido": kg_pedido,
        "lote_id": lote_id,
        "ubicacion_id": ubicacion_id or (objetivo["ubicacion_id"] if objetivo else None),
        "kg_disponible": kg_en_objetivo,
        "kg_faltante": max(faltante, 0.0),
        "calibre_requerido": calibre_requerido,
        "mensaje": (
            f"No hay stock suficiente"
            + (f" en {objetivo['ubicacion']}" if objetivo else "")
            + f": pediste {kg_pedido:.0f} kg y hay {kg_en_objetivo:.0f} kg"
            + (f" del lote {lote_id}" if lote_id else "") + "."
        ),
        "alternativas": [],
    }

    if alternativa_simple:
        resultado["alternativas"] = [{
            "lote_id": alternativa_simple["lote_id"],
            "ubicacion_id": alternativa_simple["ubicacion_id"],
            "ubicacion": alternativa_simple["ubicacion"],
            "kg_disponible": alternativa_simple["kg"],
            "calibre": alternativa_simple["calibre"],
            "categoria": alternativa_simple["categoria"],
            "requiere_traslado": alternativa_simple["ubicacion_id"].startswith("frigorifico:"),
        }]
        resultado["mensaje"] += (
            f" Se puede resolver con el lote {alternativa_simple['lote_id']} en "
            f"{alternativa_simple['ubicacion']} ({alternativa_simple['kg']:.0f} kg disponibles)."
        )
        if alternativa_simple["ubicacion_id"].startswith("frigorifico:"):
            resultado["mensaje"] += " Ojo: ese stock está en frigorífico, el retiro lleva días."
    elif combinacion:
        resultado["alternativas"] = [{
            "lote_id": f["lote_id"], "ubicacion_id": f["ubicacion_id"],
            "ubicacion": f["ubicacion"], "kg_disponible": f["kg"],
            "calibre": f["calibre"], "categoria": f["categoria"],
            "requiere_traslado": f["ubicacion_id"].startswith("frigorifico:"),
        } for f in combinacion]
        resultado["mensaje"] += (
            f" Se puede resolver combinando {len(combinacion)} lotes: "
            + ", ".join(f"{f['lote_id']} ({f['kg']:.0f} kg en {f['ubicacion']})" for f in combinacion)
        )
    else:
        resultado["mensaje"] += " No hay stock suficiente de esta variedad en ningún lado, ni combinando lotes."

    return resultado
