"""
rule_reliability.py — how much each Tier-0 reconciliation rule is carrying
right now, and how strong its own judgment call is declared to be.

`calibrado: False` on every row is deliberate: none of this is measured
against real outcomes yet — that needs diff_resolutions (see
docs/motor-conciliacion-confianza.md), which isn't wired into this
JSON-store prototype. This is the honest, present-tense version: what fires
today, and what the rule itself claims about its own strength — never
disguised as a statistic it isn't. The day diff_resolutions exists, this
swaps `fuerza_declarada` for a measured Wilson interval and flips
`calibrado` to True; the shape of the report doesn't change.
"""
from __future__ import annotations

from . import conciliacion

# Mirrors FUERZA_REGLA (frontend/src/sections/Conciliacion.jsx) and
# RULE_STRENGTH (core/confidence.py) — keep all three in sync.
FUERZA_DECLARADA = {
    "movimiento_sin_confirmar": "alta",
    "cantidad_mal_tipeada": "media",
    "merma_fisica": "media",
    "sin_explicacion": "baja",
    "tara": "alta",
}


def reporte() -> list[dict]:
    """One row per rule: how many of today's differences it explains, its
    declared strength, and the money currently riding on it."""
    counts: dict[str, dict] = {}
    for dif in conciliacion.diferencias(incluir_explicadas=True):
        clase = (dif.get("hipotesis") or {}).get("clase", "sin_explicacion")
        row = counts.setdefault(clase, {"regla": clase, "casos_abiertos": 0, "impacto_pesos": 0.0})
        row["casos_abiertos"] += 1
        row["impacto_pesos"] += float(dif.get("impacto_pesos") or 0)

    out = []
    for clase, row in counts.items():
        out.append({
            **row,
            "impacto_pesos": round(row["impacto_pesos"], 2),
            "fuerza_declarada": FUERZA_DECLARADA.get(clase, "baja"),
            "calibrado": False,
            "muestra_n": None,
        })
    out.sort(key=lambda x: -x["impacto_pesos"])
    return out
