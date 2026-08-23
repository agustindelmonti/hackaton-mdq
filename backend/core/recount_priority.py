"""
recount_priority.py — ranks open reconciliation differences by expected cost
of leaving them open, not just by money at stake.

    score = impacto_pesos * (1 - confidence) * days_open

A $2M difference the system is 80% sure about is less urgent to physically
recount than a $500K one with no explanation at all — money alone hides
that. `confidence` here is the same qualitative rule strength the frontend
already uses (FUERZA_REGLA in Conciliacion.jsx) and core/confidence.py uses
(RULE_STRENGTH) — a judgment call, not a measured statistic. The day
rule_confidence_stats (see docs/motor-conciliacion-confianza.md) is wired
in, only the source of that number changes; the formula doesn't.
"""
from __future__ import annotations

from . import conciliacion
from .fechas import hoy, parse_fecha

# Mirrors FUERZA_REGLA (frontend/src/sections/Conciliacion.jsx) and
# RULE_STRENGTH (core/confidence.py) — keep all three in sync.
CONFIDENCE_PROXY = {
    "movimiento_sin_confirmar": 0.8,
    "cantidad_mal_tipeada": 0.5,
    "merma_fisica": 0.5,
    "sin_explicacion": 0.2,
}
DEFAULT_CONFIDENCE = 0.2


def _days_open(fecha: str | None) -> int:
    f = parse_fecha(fecha)
    return max((hoy() - f).days, 0) if f else 0


def prioritized() -> list[dict]:
    """conciliacion.abiertas(), re-ranked by expected cost of staying open."""
    out = []
    for dif in conciliacion.abiertas():
        clase = (dif.get("hipotesis") or {}).get("clase")
        confidence = CONFIDENCE_PROXY.get(clase, DEFAULT_CONFIDENCE)
        days = _days_open(dif.get("fecha"))
        score = float(dif.get("impacto_pesos") or 0) * (1 - confidence) * max(days, 1)
        out.append({
            **dif,
            "confidence_proxy": confidence,
            "dias_abierto": days,
            "prioridad_score": round(score, 2),
        })
    out.sort(key=lambda x: -x["prioridad_score"])
    return out
