"""
capacity_forecast.py — projects each location's occupancy forward from its
recent intake rate, so the app can say WHEN it saturates, not just how full
it is right now.

Deterministic, on top of what already exists: conciliacion.por_ubicacion()
gives the current kg/capacidad_kg; this adds the net rate of change from the
real movements ledger over a recent window and a straight-line projection.
No model, no guess — a location whose recent trend is flat or emptying gets
no forecast at all: this never invents a saturation date for a location that
isn't actually filling up.
"""
from __future__ import annotations

import datetime
import unicodedata

from . import conciliacion, movimientos
from .fechas import hoy, parse_fecha

VENTANA_DIAS = 30  # recent window used to estimate the daily net rate


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def _net_daily_rate_kg(location_name: str, days: int = VENTANA_DIAS) -> float:
    """Net kg/day gained at this location over the recent window, from the
    real movements ledger (inflow to this destination minus outflow from
    this origin) — never a guess, only what the ledger actually shows."""
    if days <= 0:
        return 0.0
    cutoff = hoy() - datetime.timedelta(days=days)
    target = _norm(location_name)
    net = 0.0
    for m in movimientos.listar():
        f = parse_fecha(m.get("fecha"))
        if not f or f < cutoff:
            continue
        kg = float(m.get("kg") or 0)
        if _norm(m.get("destino")) == target:
            net += kg
        elif _norm(m.get("origen")) == target:
            net -= kg
    return net / days


def forecast(ventana_dias: int = VENTANA_DIAS) -> list[dict]:
    """One row per location with real capacity on file, ranked by soonest
    saturation. Locations without a capacity, or with a flat/emptying recent
    trend, are left out entirely — never a fabricated date."""
    out = []
    for u in conciliacion.por_ubicacion():
        cap = u.get("capacidad_kg")
        if not cap:
            continue
        rate = _net_daily_rate_kg(u["nombre"], ventana_dias)
        if rate <= 0:
            continue
        headroom = cap - u["kg"]
        dias = round(headroom / rate, 1) if headroom > 0 else 0.0
        out.append({
            "ubicacion_id": u["id"],
            "ubicacion": u["nombre"],
            "kg_actual": u["kg"],
            "capacidad_kg": cap,
            "ocupacion_pct": u.get("ocupacion_pct"),
            "kg_por_dia": round(rate, 1),
            "dias_hasta_saturacion": dias,
            "fecha_saturacion": (hoy() + datetime.timedelta(days=dias)).isoformat(),
            "ventana_dias": ventana_dias,
        })
    out.sort(key=lambda x: x["dias_hasta_saturacion"])
    return out
