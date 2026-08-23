"""
confidence.py — the deterministic resolver behind the `mark_confidence_claims`
tool (see angela.py TOOLS and _run_tool).

The model only names WHAT it's talking about (a movement, a count, a note, a
reconciliation rule) — this module decides HOW confident that claim actually
is, from real data. Same split of responsibility as movimientos.buscar_lote():
the model extracts language, the code resolves the fact. The model never
picks its own confidence level; if it tried to, that number wouldn't be
calibrated and would systematically mislead (see
.claude/skills/confidence-indicators/SKILL.md, "Calibration is the whole
point").

TODAY vs LATER: the JSON-store prototype doesn't have diff_resolutions /
rule_confidence_stats wired in yet (see
docs/motor-conciliacion-confianza.md), so the "reconciliation_rule" branch
below uses the same hand-set rule strength as FUERZA_REGLA in
frontend/src/sections/Conciliacion.jsx — a judgment call, not a measured
statistic. That is the ONLY branch that changes once the Supabase engine is
connected; everything else here already resolves against real records.
"""
from __future__ import annotations

import i18n
from . import movimientos, notas

# Mirrors FUERZA_REGLA in Conciliacion.jsx — keep both in sync until the real
# engine replaces this with a query against rule_confidence_stats.
RULE_STRENGTH = {
    "unconfirmed_transfer": "grounded",
    "digit_entry_error": "inferred",
    "physical_shrinkage_witnessed": "inferred",
    "no_explanation": "uncertain",
}


def resolve(reference: dict, lang: str | None = None) -> dict:
    """One claim's reference -> {"confidence": grounded|inferred|uncertain, "basis": str}."""
    def T(key, **params):
        return i18n.t(key, lang, **params)

    ref_type = reference.get("type")
    ref_id = str(reference.get("id") or "")

    if ref_type == "movement":
        m = movimientos.get_by_number(ref_id)
        if not m:
            return {"confidence": "uncertain", "basis": T("core.confidence.movement_not_found", numero=ref_id)}
        if m.get("confirmado_por"):
            return {"confidence": "grounded",
                    "basis": T("core.confidence.movement_confirmed", numero=m["numero"], quien=m["confirmado_por"])}
        return {"confidence": "inferred",
                "basis": T("core.confidence.movement_unconfirmed", numero=m["numero"])}

    if ref_type == "count":
        # A physical count is hard data by definition: someone stood in the
        # room and counted. There's no "unconfirmed" state for that.
        return {"confidence": "grounded", "basis": T("core.confidence.count", id=ref_id)}

    if ref_type == "note":
        n = notas.get_by_id(ref_id)
        if not n:
            return {"confidence": "inferred", "basis": T("core.confidence.note_not_found")}
        # Testimony, not a hard number — worth surfacing, never top-tier trust.
        return {"confidence": "inferred", "basis": T("core.confidence.note", autor=n.get("autor"))}

    if ref_type == "reconciliation_rule":
        strength = RULE_STRENGTH.get(ref_id, "uncertain")
        return {"confidence": strength, "basis": T("core.confidence.rule_no_data")}

    return {"confidence": "uncertain", "basis": T("core.confidence.no_reference")}


def resolve_claims(spans: list[dict], lang: str | None = None) -> list[dict]:
    """The full `claims` array for ConfidenceMarker, from the model's raw spans."""
    claims = []
    for i, span in enumerate(spans):
        resolved = resolve(span.get("reference") or {}, lang)
        claims.append({"id": f"c{i}", "text": span.get("text", ""), **resolved})
    return claims
