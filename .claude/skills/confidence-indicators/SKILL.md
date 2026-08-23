---
name: confidence-indicators
description: Generate a production-ready implementation of the "Confidence Indicators" AI UX pattern — scores, meters, badges, or hedging copy that show how certain an AI system is about an answer or claim, so a user can decide whether to trust, verify, or escalate. Use when the user asks to add a confidence score, trust badge, certainty meter, reliability indicator, or "how sure is the AI" UI to an AI-generated answer, recommendation, diagnosis, or hypothesis — especially in medical, financial, or other decision-support contexts where a wrong answer is costly. Reproduces the interaction and calibration discipline of the pattern, not a specific visual style; adapts to whatever framework and design system the target project already uses.
---

# Confidence Indicators

## Pattern definition

Confidence indicators are AI UX cues (scores, meters, badges, or hedging
copy) that show how certain the system is about an answer or claim. They
help users decide whether to trust, verify, or escalate. Critical when
wrong answers are costly.

**Focus: reproduce the interaction pattern and user experience, not a
specific visual design.** Adapt every implementation to the target
project's actual tech stack and design system — do not import a component
library or design language the project doesn't already use.

## When to use

Medical tools, financial analysis platforms, and decision-support systems
where a visual confidence cue helps a user assess reliability before
acting on it.

## When NOT to use

- Casual creative chat where a numeric confidence adds anxiety without
  decision value.
- When the score is not calibrated and would systematically mislead —
  see "Calibration is the whole point" below.
- On every sentence of a long answer. Prefer claim-level or answer-level
  cues, and only for the high-risk parts.

## The anti-patterns this skill exists to prevent

Every generated implementation must actively guard against these, not just
avoid them by omission:

1. **Decorating every reply with 97% confidence that never changes.** A
   confidence value with no real signal behind it is worse than none —
   it's a fabricated precision that trains users to stop reading it.
2. **Green badges on unverifiable claims with no path to sources.** If
   there's no way for the user to check the claim, the indicator must not
   read as trustworthy, no matter what the underlying score says.
3. **Hiding uncertainty behind confident tone while the model is
   guessing.** The hedging/caption copy is not optional decoration for
   low-confidence cases — it discloses *why* the score is what it is, on
   every band, including the confident one.
4. **Scores without a legend for what high vs. low means in this
   product.** A color with no explanation is decoration, not information.
   "High" for a medical diagnosis and "high" for a restaurant
   recommendation are different claims — the legend is what makes the
   color legible to *this* user in *this* product.

## Calibration is the whole point

Before writing any UI, find out what's actually driving the number:

- **A real measured signal exists** (historical accuracy of a rule, a
  retrieval score, an ensemble's agreement, a statistical test against
  known variance) → wire the component to that, and always show the
  sample size / evidence the score rests on. A score with n=2 must not
  read the same as a score with n=200 — use a real interval (e.g. a
  Wilson score interval for a proportion), not the raw ratio.
- **No real signal exists yet, only a domain expert's judgment call**
  (e.g. "this rule is usually right" hand-coded by whoever wrote it) →
  that is legitimate information, but it is not a measured statistic.
  Say so explicitly in the copy ("the rule's own judgment call, not yet
  measured against real cases") instead of dressing it up as a
  percentage. Never synthesize a fake score just to make a badge show a
  number.
- **Neither exists** → the indicator must default to its lowest-trust,
  unverified state. Do not ask an LLM to estimate its own confidence as
  a substitute for a calibrated signal — that number is usually not
  calibrated and will systematically mislead (this is explicitly one of
  the "when NOT to use" cases above).

## Interaction requirements (implement all of these)

- **Core interaction**: a score/meter/badge showing how sure the system
  is, driven by real data per the calibration rules above.
- **All four interaction states**: `idle` (nothing to show yet — render
  nothing, don't fake a state), `loading` (announce via `aria-live`, don't
  just silently hang), `error` (with a retry path, distinct in tone from
  the domain's own "this is wrong" color), `success` (the real indicator).
- **A legend** explaining what each band means in this specific product,
  reachable via click and keyboard, not just hover-only (hover-only is
  unreachable by keyboard and touch).
- **A path to evidence/sources** for any band above the lowest trust
  level — a link, a callback that opens the supporting detail, anything
  that lets the user actually verify the claim.
- **Hedging copy** that states the sample size or the nature of the
  signal (measured vs. judgment call vs. unverified) on every band, not
  hidden behind a tooltip only the curious will find.
- **Keyboard support**: the trigger is a real focusable control; Escape
  closes an open legend/popover and returns focus to the trigger;
  click-outside also closes it.
- **ARIA**: `aria-haspopup`/`aria-expanded`/`aria-controls` on the
  trigger, `role="dialog"` (or an equivalent landmark) with an accessible
  name on the legend panel, `aria-live="polite"` on the loading state.
  Prefer a native element where one exists with the right semantics for
  free (e.g. HTML `<meter>` for a meter variant) over a hand-rolled div.

## Reference implementation in this repo

A worked, running example lives in this project:

- `frontend/src/components/ConfidenceIndicator.jsx` — the reusable
  component (React + this project's Tailwind v4 token system), with the
  calibration guards, all four states, badge and meter variants, a
  keyboard-accessible legend popover, and the qualitative-vs-measured
  distinction described above.
- `frontend/src/sections/Conciliacion.jsx` (see `FUERZA_REGLA`) — the real
  production integration: today the backend only has hand-set rule
  strength (no measured stats yet), so every badge on that screen renders
  through the *qualitative* path — an honest reflection of where the
  system's confidence engine actually is right now. See
  `docs/motor-conciliacion-confianza.md` for the plan to replace that with
  real calibrated scores (Wilson intervals over resolved cases).
- `frontend/confidence-indicator-demo.html` /
  `frontend/src/confidence-indicator-demo.jsx` — a standalone, dev-only
  page exercising every state, band, and anti-pattern guard with real
  interaction (not screenshots). Run `npm run dev` inside `frontend/` and
  open `/confidence-indicator-demo.html`.

When generating an implementation in *this* repo, extend or reuse
`ConfidenceIndicator.jsx` rather than writing a new one from scratch.

## Steps to generate an implementation in a new project

1. **Identify the target stack and design system** — framework, styling
   approach (CSS-in-JS, Tailwind, CSS modules, a component library),
   existing color/semantic tokens, existing i18n setup if any. Reuse them;
   don't introduce a new one.
2. **Find or ask what the real confidence signal is.** Do not skip this —
   it determines almost everything else. If the caller can't say, default
   the design to the qualitative/unverified path (see "Calibration is the
   whole point") rather than inventing a number.
3. **Design the states** (idle/loading/error/success) and the band
   thresholds (how many bands, what score/sample-size combination puts a
   claim in which band). Write the thresholds as plain, auditable code —
   never let an LLM call decide the band at render time.
4. **Build the component**: trigger + optional meter + legend popover +
   hedge caption + evidence link, with the ARIA/keyboard requirements
   above. Reuse the target project's existing semantic colors if it has
   them (e.g. a color already meaning "success"/"warning"/"error" in that
   product) instead of inventing a new palette.
5. **Wire in the anti-pattern guards** as code, not as a comment someone
   might delete: no legend → dev warning + generic fallback copy, never a
   silent ship; no evidence path → force the lowest-trust band regardless
   of score; no sample size → never print a bare percentage.
6. **Verify by actually running it** — render every state/band
   combination and confirm keyboard and screen-reader behavior, not just
   that it compiles. A component that only "looks right" in one state is
   not done.
