"""
inconsistencias_papasud.py · "Arreglar el pasado" — el detector de lo que está
roto en la operación real de Papasud, tan valioso como el importador mismo
(PLAN_TRACKS_PAPASUD.md, Track B §3).

Todo determinista: cada hallazgo cita el/los movimiento(s) exacto(s) que lo
sostienen, nunca una sospecha genérica.
"""
from __future__ import annotations

import datetime

from . import modelo_real as M


def detectar() -> list[dict]:
    hallazgos: list[dict] = []
    hallazgos += _remitos_duplicados()
    hallazgos += _sin_dtv()
    hallazgos += _fechas_incoherentes()
    hallazgos += _tarjeta_cruzada()
    hallazgos += _kilos_no_cierran_en_frigorifico()
    hallazgos += _linaje_multivariedad()
    hallazgos += _movimientos_sin_confirmar()
    return hallazgos


def _remitos_duplicados() -> list[dict]:
    por_remito: dict[str, list[dict]] = {}
    for m in M.movimientos():
        por_remito.setdefault(m["remito"], []).append(m)
    out = []
    for remito, movs in por_remito.items():
        if len(movs) > 1:
            out.append({
                "tipo": "remito_duplicado",
                "gravedad": "alta",
                "titulo": f"Remito {remito} usado {len(movs)} veces",
                "detalle": f"El remito {remito} aparece en {len(movs)} movimientos distintos.",
                "movimientos": [m["numero"] for m in movs],
            })
    return out


def _sin_dtv() -> list[dict]:
    out = []
    for m in M.movimientos():
        if m.get("dtv") is None:
            out.append({
                "tipo": "sin_dtv",
                "gravedad": "media",
                "titulo": f"Movimiento {m['numero']} sin DTV",
                "detalle": (
                    f"{m['tipo']} del lote {m['lote_id']} ({m['kg']:.0f} kg) desde "
                    f"{m['origen_nombre']} a {m['destino_nombre']} el {m['fecha']} "
                    f"no tiene DTV registrado."
                ),
                "movimientos": [m["numero"]],
            })
    return out


def _fechas_incoherentes() -> list[dict]:
    out = []
    primer_ingreso: dict[str, str] = {}
    for m in M.movimientos():
        if m["tipo"] == "ingreso_tolva":
            actual = primer_ingreso.get(m["lote_id"])
            if actual is None or m["fecha"] < actual:
                primer_ingreso[m["lote_id"]] = m["fecha"]

    for m in M.movimientos():
        ingreso = primer_ingreso.get(m["lote_id"])
        if ingreso and m["fecha"] < ingreso:
            out.append({
                "tipo": "fecha_incoherente",
                "gravedad": "alta",
                "titulo": f"Movimiento {m['numero']} fechado antes del ingreso del lote",
                "detalle": (
                    f"{m['tipo']} del lote {m['lote_id']} está fechado {m['fecha']}, "
                    f"pero el lote recién ingresó a planta el {ingreso}."
                ),
                "movimientos": [m["numero"]],
            })
    return out


def _tarjeta_cruzada() -> list[dict]:
    """Como en las notas de P.Chica: 'tienen tarjetas del lote 52 pero
    corresponden al lote 50'. Detecta movimientos donde la tarjeta declarada
    no es la del lote que dice el sistema."""
    out = []
    lotes = {l["id"]: l for l in M.lotes()}
    for m in M.movimientos():
        tarjeta = m.get("tarjeta_declarada")
        if not tarjeta:
            continue
        lote = lotes.get(m["lote_id"])
        if lote and tarjeta != lote["tarjeta"]:
            lote_de_la_tarjeta = next(
                (l["id"] for l in lotes.values() if l["tarjeta"] == tarjeta), None)
            out.append({
                "tipo": "tarjeta_cruzada",
                "gravedad": "alta",
                "titulo": f"Tarjeta cruzada en {m['numero']}",
                "detalle": (
                    f"El movimiento {m['numero']} del lote {m['lote_id']} usó la "
                    f"tarjeta {tarjeta}, que corresponde al lote "
                    f"{lote_de_la_tarjeta or '??'}. Identificación física no coincide "
                    f"con lo declarado."
                ),
                "movimientos": [m["numero"]],
            })
    return out


def _kilos_no_cierran_en_frigorifico() -> list[dict]:
    """Para cada (lote, frigorífico): lo que entró (envio_frio) tiene que ser
    >= lo que salió (retiro_frio + lo que sigue guardado). Si retiraron más de
    lo que había entrado, esos kilos no existen."""
    entrado: dict[tuple[str, str], float] = {}
    salido: dict[tuple[str, str], float] = {}
    movs_por_par: dict[tuple[str, str], list[dict]] = {}

    for m in M.movimientos():
        if m["tipo"] == "envio_frio":
            key = (m["lote_id"], m["destino_id"])
            entrado[key] = entrado.get(key, 0.0) + m["kg"]
            movs_por_par.setdefault(key, []).append(m)
        elif m["tipo"] == "retiro_frio":
            key = (m["lote_id"], m["origen_id"])
            salido[key] = salido.get(key, 0.0) + m["kg"]
            movs_por_par.setdefault(key, []).append(m)

    out = []
    for key, sal in salido.items():
        ent = entrado.get(key, 0.0)
        if sal > ent + 0.5:
            lote_id, ubic_id = key
            out.append({
                "tipo": "kilos_no_cierran",
                "gravedad": "alta",
                "titulo": f"El lote {lote_id} retiró más kilos de los que entraron a {M.nombre_ubicacion(ubic_id)}",
                "detalle": (
                    f"Entraron {ent:.0f} kg y se retiraron {sal:.0f} kg del lote "
                    f"{lote_id} en {M.nombre_ubicacion(ubic_id)}: sobran "
                    f"{sal - ent:.0f} kg que no tienen origen."
                ),
                "movimientos": [m["numero"] for m in movs_por_par[key]],
            })
    return out


def _linaje_multivariedad() -> list[dict]:
    """Regla dura de INASE: un lote, una sola variedad. Si el dataset (o algo
    importado) trae el mismo código de lote con variedades distintas, es un
    error de linaje, no una discrepancia de stock."""
    variedad_por_lote: dict[str, set] = {}
    for l in M.lotes():
        variedad_por_lote.setdefault(l["id"], set()).add(l["variedad_id"])
    out = []
    for lote_id, variedades in variedad_por_lote.items():
        if len(variedades) > 1:
            out.append({
                "tipo": "linaje_multivariedad",
                "gravedad": "critica",
                "titulo": f"El lote {lote_id} tiene más de una variedad cargada",
                "detalle": (
                    f"El lote {lote_id} aparece con variedades {sorted(variedades)}. "
                    f"Un lote es una sola variedad — violación de la regla de linaje INASE."
                ),
                "movimientos": [],
            })
    return out


def _movimientos_sin_confirmar(dias_umbral: int = 3) -> list[dict]:
    hoy = _hoy()
    out = []
    for m in M.movimientos():
        if not m.get("confirmado_en_destino", True):
            try:
                f = datetime.date.fromisoformat(m["fecha"])
            except (TypeError, ValueError):
                continue
            dias = (hoy - f).days
            if dias >= dias_umbral:
                out.append({
                    "tipo": "sin_confirmar_en_destino",
                    "gravedad": "media",
                    "titulo": f"Movimiento {m['numero']} sin confirmar hace {dias} días",
                    "detalle": (
                        f"{m['kg']:.0f} kg del lote {m['lote_id']} salieron de "
                        f"{m['origen_nombre']} hacia {m['destino_nombre']} el {m['fecha']} "
                        f"y todavía nadie confirmó la llegada."
                    ),
                    "movimientos": [m["numero"]],
                })
    return out


def _hoy() -> datetime.date:
    import os
    valor = os.environ.get("POLPILOT_DEMO_TODAY", "").strip() or "2026-08-22"
    return datetime.date.fromisoformat(valor)
