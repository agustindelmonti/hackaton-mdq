---
tags: [reference, design, ux, papasud, hackathon]
created: 2026-08-21
event: Cursor Hackathon Mar del Plata 2026-08-22
status: implementable-spec
---

# Voice-First Field-Ops App — Design & UX Spec

Implementable design direction for a mobile-first, Spanish-language, voice-first
operations app for a seed-potato producer (Papasud). Written for a ~3h build with a
5-minute judged demo. Format throughout: **pattern → why → how**.

> Scope note: the palette in §5 is a *proposed* direction. Two existing projects are
> being audited for reusable tokens/components in parallel — if one of them already has
> a warm-neutral + semantic-status system, reconcile by keeping the existing neutral
> ramp and importing only the **semantic status colors** (§5.3), which are the part that
> carries meaning in this app.

---

## 0. The one design idea that ties it together

**Colour encodes epistemic status, not decoration.**

| Meaning | Colour role | Where it appears |
|---|---|---|
| The machine *heard / inferred* this | `cielo` (steel blue) | live transcript, parsed field chips, AI hypothesis |
| A human *confirmed* this | `brote` (green) | confirmed movement, synced badge |
| The machine is *unsure* — needs a human | `ocre` (amber) | low-confidence field, clarifying question |
| Something is *wrong* | `ladrillo` (clay red) | discrepancy alert, failed sync |

This is the single highest-leverage decision in the whole spec. It makes the demo
narratable in one sentence ("blue is what the AI thinks, green is what a person
confirmed, amber is what it's asking about") and it gives judges a legible mental model
in the first 20 seconds. Everything below is downstream of it.

---

## 1. Voice-first mobile UX patterns

### 1.1 Recording affordance: tap-to-toggle, not push-to-hold

**Pattern.** A single large circular button. Tap to start, tap to stop. Show elapsed
time while recording. Provide a **cancel** target (swipe-away or an X) distinct from stop.

**Why.** Push-to-hold (WhatsApp/Wispr-style hold-a-hotkey) is excellent for 2-second
bursts on a keyboard, but it fails this exact user: a warehouse worker dictating a
15–25-word Spanish sentence, one-handed, possibly gloved, possibly setting the phone
down on a pallet. Holding a finger precisely on a target for 20s while talking and
walking is a dexterity tax. Toggle also survives the demo: you can start recording and
gesture at the projector with your hand off the phone.

**How.** Give the toggle a hard state machine — `idle → recording → transcribing →
parsed → confirming → saved`. Never let two states be visually ambiguous; each state
gets its own label text *and* its own colour *and* its own icon. Add haptics
(`navigator.vibrate(15)`) on start/stop — cheap, and it reads as craft on a real device.

```
idle         ⬤ mic     "Tocá para hablar"        tierra-800 fill
recording    ⬛ stop    "Escuchando… 0:07"        ladrillo-500 fill + pulse ring + bars
transcribing ⟳ spinner "Transcribiendo…"         cielo-500 fill
parsed       ✓ check   "Revisá y confirmá"       cielo-500 outline
```

Do **not** implement push-to-talk as a fallback. One affordance, done well.

### 1.2 Live amplitude feedback: bars, not a scrolling waveform

**Pattern.** 24–32 vertical bars, centre-anchored, driven by real microphone amplitude
at 60fps. Not a scrolling seismograph.

**Why.** The bar visualiser's only job is answering "is it hearing me?" in under 300ms.
A scrolling waveform costs more code, is harder to read at a glance, and looks worse
scaled up on a projector. Bars read as intentional design; a canvas waveform reads as a
library default. Critically: **it must be driven by real audio**, because a faked
animation looks identical when you're silent, and a judge who says "let me try" will
catch it instantly.

**How.** `getUserMedia` → `AnalyserNode` with `fftSize = 64` → `getByteFrequencyData`
into a `Uint8Array` inside a `requestAnimationFrame` loop, mapped to bar heights. Full
sketch in §7.2. ([MDN: AnalyserNode.getByteFrequencyData](https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/getByteFrequencyData))

### 1.3 Live vs. final transcription: two visually distinct tiers

**Pattern.** Interim (unstable) transcript renders in a lighter weight and lower-opacity
colour; finalised segments snap to full-contrast body text. Never let text change colour
*and* reflow at the same moment.

**Why.** Interim results from any streaming ASR churn — words get replaced. If interim
text looks identical to final text, the user watches their sentence "glitch" and loses
trust in the system. Rendering instability as visibly provisional converts a bug into a
feature: the user reads it as the machine thinking.

**How.** With the Web Speech API, `SpeechRecognition` results carry `isFinal`. Render
final segments into one span, the current interim into a second span at
`text-tierra-500 italic`. If you're using a server-side model (Whisper / a Cursor-side
transcribe call), you have no interim results — in that case **skip the fake live
transcript entirely** and go straight from the bar visualiser to a 600ms
"Transcribiendo…" state. A fake typewriter effect is the single most common tell of a
hackathon demo; the amplitude bars already carry the liveness burden.

### 1.4 ⭐ The confirm-parsed-result pattern (the centrepiece)

This is the highest-value UI in the whole app. It is what makes it look like an
*operational tool* rather than a chatbot. Get this right and skip something else.

**Pattern — "sentence on top, fields below, one tap to fix."**

```
┌──────────────────────────────────────────┐
│ ❝ moví 12 bolsones del lote 42 del       │  ← verbatim transcript, quoted,
│   frigorífico A al galpón 2 ❞            │    small, muted, tap to replay audio
├──────────────────────────────────────────┤
│ MOVIMIENTO DE STOCK              ● 96%   │  ← inferred intent + overall confidence
├──────────────────────────────────────────┤
│ Cantidad      12 bolsones            ›   │  ← each row: LABEL / value / chevron
│ Lote          42 · Spunta 2025-G     ›   │  ← resolved entity, shows enrichment
│ Origen        Frigorífico A          ›   │
│ Destino       Galpón 2               ›   │
│ ⚠ Fecha       ¿hoy 21/08?            ›   │  ← LOW CONFIDENCE: amber, question form
├──────────────────────────────────────────┤
│ ⚠ Galpón 2 queda a 87% de capacidad      │  ← proactive consequence, not an error
├──────────────────────────────────────────┤
│  [ Corregir ]        [ Confirmar ✓ ]     │  ← 56px tall, primary right
└──────────────────────────────────────────┘
```

**Why each part earns its place:**

- **Verbatim transcript on top, in quotes.** The audit trail. It lets the user (and the
  judge) verify the mapping from speech → structure themselves. This is the trust
  primitive: without it, the parsed fields are unfalsifiable magic. Expense-capture and
  receipt-OCR tools all do this (show the receipt image beside the extracted fields) —
  same principle, different modality. Make it tappable to re-play the audio.
- **Label / value / chevron rows, not a form.** The default instinct is to render an
  editable form with five inputs. Resist it. A form says "you must now do data entry" —
  which destroys the entire value proposition of voice. Read-only rows with a chevron
  say "this is done; tap only if it's wrong." Cost of the happy path drops from five
  interactions to one.
- **Resolved entities, not echoed strings.** "Lote 42" alone proves nothing. "Lote 42 ·
  Spunta 2025-G" proves the system *looked it up in a real dataset* and matched. This
  one detail is worth more to a judge than any animation: it demonstrates grounding.
- **Amber on the uncertain field only.** Directs attention. One amber row on a card of
  five green-neutral rows creates an unmissable focal point.
- **The consequence line.** "Galpón 2 queda a 87% de capacidad" shows the system
  understands the *domain*, not just the sentence. Very cheap to compute, very high
  perceived intelligence.

**How.** One `Card`, a header, a `<dl>`-ish list of rows, a footer with two buttons.
Tapping a row opens a `Drawer` (bottom sheet) containing *only that field's* editor —
usually a list of valid options (the four locations, the known lots), not a text input.
Editing by picking from a constrained set is 3x faster than typing and cannot produce
invalid data. On confirm, the card animates into the movements feed. Code in §7.3.

### 1.5 Confidence display: show it sparingly and never as a raw float

**Pattern.** Two tiers only. **High** → render normally, no confidence indicator at all.
**Low** (below your threshold, ~0.75) → amber left-border on that row, a warning glyph,
and the value rewritten **as a question**. Optionally one overall percentage in the card
header as a small filled dot + number.

**Why.** Per-field percentages on every row are noise: they force the user to do
arithmetic on five numbers to decide where to look. Worse, showing `0.83` on a field
that is in fact correct teaches the user to distrust correct data. Confidence is only
actionable at the point where it changes behaviour — so only render it there. The single
header number exists purely as a legibility cue that the system *has* a calibrated
notion of certainty (and it demos well).

**How.** If the extraction model gives you per-field logprobs, use them. If it doesn't
(likely, in 3 hours), have the model emit confidence itself in the JSON schema —
`{ value, confidence: "high" | "low", question?: string }` per field. Ask for a
`question` string only when `confidence` is `"low"`. This is one extra schema field and
it does all the work.

### 1.6 Ask, don't guess — the clarifying question pattern

**Pattern.** When a field is genuinely ambiguous or missing, do **not** fill it with a
guess and mark it amber. Render the row as an inline question with **2–3 tappable
answer chips** and no free-text option.

```
⚠  ¿Qué frigorífico?     [ Frigorífico A ]  [ Frigorífico B ]
```

**Why.** A guessed value invites confirmation bias — a tired user taps Confirmar and the
wrong data lands. A question cannot be accidentally confirmed. And chips make answering
a *single tap*, so asking costs the user almost nothing, which means you can afford to
ask rather than guess. The demo line here is strong: "when it isn't sure, it asks
instead of guessing" — that is a maturity signal judges respond to.

**How.** Disable the primary `Confirmar` button while any question row is unanswered
(and label it `Falta 1 dato` rather than just greying out — always say why a button is
disabled). Answering a chip resolves the row to a normal green-neutral row and enables
confirm. Constrain chips to entities that actually exist in your seed data.

### 1.7 Latency choreography

**Pattern.** Never show a bare spinner for the transcribe+parse round trip. Show
**staged, labelled progress**: `Transcribiendo…` → `Entendiendo…` → `Buscando lote 42…`.

**Why.** A 2–4s LLM call feels twice as long under an unlabelled spinner. Naming the
stage makes the wait feel like work being done, and — importantly for the demo — it
narrates your architecture out loud without you having to say it.

**How.** Three hardcoded stage labels on timers is acceptable if the real stages aren't
individually observable. Ensure the last stage mentions a *specific* entity from the
utterance; that's what makes it feel real.

---

## 2. Industrial / field-worker mobile UI constraints

The user is in a cold-store or a shed: gloves, dust, glare, one hand occupied, bad
signal. This section is where most consumer-app instincts are actively wrong.

### 2.1 Touch targets: 56px minimum, 64px for primary

**Why.** WCAG 2.2 sets 24×24 CSS px as the AA floor and 44×44 as AAA
([2.5.8 Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
[2.5.5 Enhanced](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)).
Platform guidance sits at 44pt (Apple HIG) / 48dp (Material 3). **All of those assume a
bare fingertip on a clean screen indoors.** A gloved finger has a contact patch roughly
1.5–2x wider and no tactile precision, and the user isn't looking at the screen the
whole time. So treat 44–48px as the *floor*, not the target.

**How.**
- Primary action (mic button): **96px** diameter. It is the only thing on the screen.
- Primary buttons: `h-14` (56px), full-width.
- Rows / list items: `min-h-16` (64px) — also gives room for two lines of text.
- Secondary/icon buttons: `h-12 w-12` (48px) absolute minimum, and **never adjacent** to
  a destructive action. Put ≥12px of dead space between any two targets.
- **No destructive action without a confirm step**, and never place `Cancelar` next to
  `Confirmar` at the same visual weight — a mis-tap in a cold store must not delete a
  stock movement.

### 2.2 Sunlight legibility: high contrast, dark-on-light for outdoors

**Why.** Direct sunlight and dusty/greasy screens both flatten perceived contrast. Two
consequences: (a) subtle greys vanish entirely — a `#9CA3AF` label on white is invisible
outdoors; (b) glossy dark themes become mirrors, so **dark mode is worse outdoors**
despite being better in a cold store.

**How.**
- **Default to the light theme** for this app; offer dark as a toggle. (For the
  projector demo, see §6 — you may want the opposite.)
- Body text and all data values: minimum **7:1** contrast, not 4.5:1. In practice: no
  text lighter than `tierra-600` (#5C564A) on `tierra-50`.
- **Never encode meaning in colour alone** — every status carries an icon and a word.
  This is both an accessibility requirement and a glare requirement.
- Avoid low-alpha overlays and thin hairline borders (`1px` at 10% opacity disappears).
  Use `1.5px` borders at ≥20% opacity, or lean on background-fill separation instead.
- Avoid pure white `#FFFFFF` on large surfaces — it blooms in sunlight. `#FAF8F5` reads
  as white while being marginally kinder.

### 2.3 One-handed use: everything interactive in the bottom two-thirds

**Why.** The phone is held in one hand while the other holds a pallet jack, a clipboard,
or a bolsón. The top ~25% of a modern phone screen is unreachable by thumb without
regripping — and regripping while holding something is how phones get dropped.

**How.**
- Mic button: fixed bottom centre, above the safe-area inset.
- Primary confirm/cancel: bottom of the card, not the top.
- Top bar is **display-only** — location name, sync status, connectivity. No controls.
- Navigation: a bottom tab bar (`Voz` / `Stock` / `Alertas`), 3 items max, 64px tall.
- Sheets/drawers rise from the bottom (`Drawer`, not `Dialog`) so their controls land in
  the thumb zone.

### 2.4 Type scale: 17px body floor, tabular numerals for data

**Why.** 14px body text is standard on the web and unreadable at arm's length in a shed.
Numbers are the payload of this app — quantities, lot numbers — and proportional digits
make columns of numbers jitter and make transposition errors (12 vs 21) harder to catch.

**How.** Body 17px minimum, labels 13px but uppercase + tracked + high contrast (small
type survives only if it's also high-contrast), data values 20–28px semibold with
`font-variant-numeric: tabular-nums`. Full scale in §5.4.

### 2.5 Spotty connectivity is a design constraint, not an error state

Covered in §3. The key framing: **offline is the normal case**, not the exception. A
cold-store has concrete walls. Never block the mic button on network state.

---

## 3. Offline-first / optimistic-UI status patterns

**Pattern — a three-state badge with distinct shape, colour, icon, and word.** The
action always succeeds locally and immediately; the badge tells the truth about
durability afterwards.

| State | Visual | Copy (es) | Behaviour |
|---|---|---|---|
| Pending | amber, hollow outline, clock icon, subtle pulse | `Pendiente` | queued locally, will retry |
| Synced | green, filled, check icon, no animation | `Sincronizado` | confirmed server-side |
| Failed | clay red, filled, alert icon, **tappable** | `Sin enviar · Reintentar` | manual retry available |

**Why.**
- **Optimistic-first.** If the worker has to wait for a round trip to see their movement
  recorded, the app is unusable in a cold store. Write to local state, render
  immediately, reconcile in the background. ([web.dev — Offline UX design
  guidelines](https://web.dev/articles/offline-ux-design-guidelines): queue tasks rather
  than blocking with modals, and "tell the user what state their data is in.")
- **Pending must look *calm*, not alarming.** Amber-hollow with a slow pulse reads as
  "in flight." A red error or a blocking spinner for something that is working correctly
  trains the user to ignore status entirely.
- **Only failure is interactive.** If pending and failed are both tappable, the user
  taps pending items pointlessly. Making tappability itself a signal means the one thing
  that needs a human is the one thing that invites a touch.
- **Shape + icon + word, never colour alone.** Glare, dust, and colour-blindness all
  break colour-only encoding (§2.2).

**How.**
- Global connectivity chip in the top bar: `● En línea` / `◐ Sin conexión · 3 pendientes`.
  Show the *count*, not just the state — the count is what the user actually needs.
- Per-row badge on each movement in the feed.
- On reconnect, animate pending→synced with a short stagger (~80ms apart). This is a
  4-line effect and it is one of the best demo moments available: toggle the network off,
  dictate two movements, toggle back on, watch them all flip to green.
- Absolutely do **not** build a real service worker / IndexedDB sync engine in 3 hours.
  A Zustand store with a `status` field per record plus a fake 900ms `setTimeout`
  reconcile is visually indistinguishable and costs 10 minutes. Add a dev-only
  "Modo sin conexión" switch so you can trigger it on stage.
- One extra credibility detail if you have 5 spare minutes: show `Última sincronización:
  hace 2 min` in the top bar. Timestamps read as operational software.

---

## 4. Discrepancy / anomaly alert UI

The mature versions of this pattern live in observability (an incident + a suspected
cause), fraud detection (a flagged transaction + risk reasons), and finance
reconciliation (a variance + a suggested match). What they share, and what a chatbot
answer lacks, is a **fixed four-part anatomy**.

**Pattern — Anomaly card: What / Evidence / Hypothesis / Actions.**

```
┌──────────────────────────────────────────────────┐
│ ⚠  DISCREPANCIA DE STOCK          Confianza: Media│  ← 1. WHAT: magnitude first
│    Lote 42 · Frigorífico A                        │
│    Faltan 8 bolsones  (esperado 120 · contado 112)│
├──────────────────────────────────────────────────┤
│ EVIDENCIA                                         │  ← 2. EVIDENCE: 3 timestamped
│ • 19/08 14:02  Ingreso  +120  (remito R-8841)     │     facts, each linkable
│ • 20/08 09:15  Egreso    −8   sin remito  ⚠       │
│ • 21/08 07:40  Conteo físico  112                 │
├──────────────────────────────────────────────────┤
│ ⌕ HIPÓTESIS                                       │  ← 3. HYPOTHESIS: hedged,
│ El egreso del 20/08 no tiene remito asociado y    │     specific, cites evidence,
│ coincide exactamente con el faltante. Probable-   │     visually marked as AI
│ mente se cargó a Galpón 2 sin registrar el        │
│ traslado.                                         │
│                              ── generado por IA   │
├──────────────────────────────────────────────────┤
│ [ Ver en Galpón 2 ]  [ Ajustar ]  [ Escalar ]     │  ← 4. ACTIONS: 3, ordered
└──────────────────────────────────────────────────┘
```

**Why each part:**

1. **Magnitude before narrative.** "Faltan 8 bolsones" with expected-vs-counted is the
   thing a manager needs in one glance. Leading with prose is the most common failure
   mode of AI-generated alerts.
2. **Evidence trail is what makes the hypothesis credible.** This is the crux: an
   unsourced AI explanation is an opinion; the *same sentence* with three timestamped
   records above it is an argument the user can check. Every mature anomaly UI does this
   — the raw signals sit beside the interpretation, and the interpretation points at
   them. If you cut anything from this card, do not cut the evidence list.
3. **The hypothesis must be visually fenced off as machine-generated** (blue `cielo`
   left border, a distinct icon, a `generado por IA` footer) and must be **hedged in
   language** — "Probablemente", "coincide con". An AI cause stated as fact is a
   liability; stated as a hypothesis with cited evidence it is genuinely useful. Note
   that the hypothesis here does the specific, checkable thing: it points at *one named
   record* and explains *why that record*.
4. **Confidence as a three-tier word, not a number.** `Alta / Media / Baja` in the
   header. A number invites false precision arguments; a word sets expectations.
5. **Exactly three actions, in escalating cost.** Investigate (cheap, read-only) →
   Correct (writes data) → Escalate (involves a human). Anomaly UIs that end without an
   action are dashboards; ones that end with an action are tools. Put the cheapest,
   most-likely action first — that's the one that makes the demo flow, because
   `Ver en Galpón 2` navigates you straight to the screen that proves the hypothesis
   right, which is a *fantastic* 30 seconds of demo.

**How.** One `Card` with four stacked sections separated by `Separator`. Evidence rows
are a plain list with `tabular-nums` timestamps and an amber glyph on the anomalous row.
Hypothesis is a `border-l-4 border-cielo-500 bg-cielo-50` block. Actions are a
`grid-cols-3 gap-2` of `h-14` buttons: first `variant="default"`, other two
`variant="outline"`. Seed the data so the hypothesis is *provably* right when the judge
follows the first action.

---

## 5. Proposed visual direction — "Tierra & Brote"

### 5.1 Rationale

The failure mode to avoid is the purple/indigo gradient + glassmorphism + glow look. It
signals "AI demo," and to a family-run potato business it signals "not for us." Judges
have seen forty of them by noon.

Instead: **warm earth neutrals + a saturated seed-green + a functional amber/clay**.
Rationale in one line each —

- **Warm neutrals with an olive/brown cast** (rather than the standard cool blue-grey
  `slate`) instantly read as agricultural without a single illustration or emoji. It's
  the cheapest possible way to look like it belongs to this company.
- **A deep, saturated green** as primary reads both "agricultural" and "confirmed/OK",
  letting one colour do brand and semantic duty. Deep and slightly desaturated (not
  neon lime) keeps it looking industrial rather than eco-consumer.
- **Amber and clay red** are the natural earth-palette neighbours of "attention" and
  "wrong," so the semantic layer is harmonious rather than bolted on.
- **A steel blue** is the one non-earth hue, reserved exclusively for the machine's own
  voice (§0). Because it's the only cool colour in the system, anything AI-generated is
  identifiable at a glance, from across a room, on a projector.
- Squarer radii (10px, not 20px) and flat fills with crisp 1.5px borders read as
  operational software. Heavy shadows and big pills read as consumer app.

### 5.2 Ready-to-paste Tailwind v4 tokens

Tailwind v4 defines design tokens via `@theme`; every variable there becomes a utility
and a CSS custom property ([Tailwind — theme variables](https://tailwindcss.com/docs/theme)).
Paste this whole block into `app/globals.css` under `@import "tailwindcss";`.

```css
@import "tailwindcss";

@theme {
  /* ── Neutrals: warm earth (replaces slate/gray) ───────────────── */
  --color-tierra-50:  #FAF8F5;
  --color-tierra-100: #F2EEE8;
  --color-tierra-200: #E4DED4;
  --color-tierra-300: #CFC7B9;
  --color-tierra-400: #A79E8D;
  --color-tierra-500: #7D7566;
  --color-tierra-600: #5C564A;
  --color-tierra-700: #423E35;
  --color-tierra-800: #2B2823;
  --color-tierra-900: #1A1815;
  --color-tierra-950: #100F0D;

  /* ── Brote (seed green): brand + CONFIRMED / SYNCED ───────────── */
  --color-brote-50:  #ECF7F0;
  --color-brote-100: #D2ECDB;
  --color-brote-200: #A9DCBB;
  --color-brote-300: #7CC698;
  --color-brote-400: #47AC72;
  --color-brote-500: #1F7A46;
  --color-brote-600: #196438;
  --color-brote-700: #135029;
  --color-brote-800: #0E3B1F;
  --color-brote-900: #0B2E1B;

  /* ── Cielo (steel blue): MACHINE-GENERATED / PARSED / AI ──────── */
  --color-cielo-50:  #EDF4F8;
  --color-cielo-100: #D3E4EF;
  --color-cielo-200: #A9CBDF;
  --color-cielo-300: #7FB4D2;
  --color-cielo-400: #4B8FB4;
  --color-cielo-500: #2C6E8F;
  --color-cielo-600: #235A76;
  --color-cielo-700: #1A4459;
  --color-cielo-800: #133342;
  --color-cielo-900: #0E2632;

  /* ── Ocre (amber): LOW CONFIDENCE / PENDING / NEEDS REVIEW ────── */
  --color-ocre-50:  #FDF6E8;
  --color-ocre-100: #FAE9C4;
  --color-ocre-200: #F3D68F;
  --color-ocre-300: #E8B75B;
  --color-ocre-400: #D89B2E;
  --color-ocre-500: #B47A15;
  --color-ocre-600: #94620F;
  --color-ocre-700: #714A0B;

  /* ── Ladrillo (clay red): DISCREPANCY / FAILED ────────────────── */
  --color-ladrillo-50:  #FCEEEA;
  --color-ladrillo-100: #F8D8CF;
  --color-ladrillo-200: #F0B3A2;
  --color-ladrillo-300: #E28870;
  --color-ladrillo-400: #CE5C3F;
  --color-ladrillo-500: #B03C24;
  --color-ladrillo-600: #92301C;
  --color-ladrillo-700: #712314;

  /* ── Type scale (mobile-first, 17px body floor) ───────────────── */
  --text-label:   0.8125rem;  /* 13px — UPPERCASE + tracked only  */
  --text-label--line-height: 1.15;
  --text-label--letter-spacing: 0.06em;
  --text-label--font-weight: 600;
  --text-sm:      0.9375rem;  /* 15px — captions, timestamps      */
  --text-base:    1.0625rem;  /* 17px — BODY FLOOR                */
  --text-base--line-height: 1.5;
  --text-lg:      1.1875rem;  /* 19px — row values, card titles   */
  --text-data:    1.5rem;     /* 24px — quantities, stock numbers */
  --text-data--line-height: 1.1;
  --text-data--font-weight: 650;
  --text-xl:      1.75rem;    /* 28px — hero metric               */
  --text-2xl:     2.25rem;    /* 36px — screen title / big number */

  /* ── Spacing / radius / shadow ────────────────────────────────── */
  --spacing: 0.25rem;         /* 4px base unit                    */
  --radius-sm:  0.375rem;     /* 6px  — chips, badges             */
  --radius-md:  0.625rem;     /* 10px — cards, buttons (default)  */
  --radius-lg:  0.875rem;     /* 14px — sheets, drawers           */
  --radius-xl:  1.25rem;      /* 20px — use sparingly             */
  --shadow-card:  0 1px 2px 0 rgb(16 15 13 / 0.06),
                  0 1px 3px 0 rgb(16 15 13 / 0.04);
  --shadow-sheet: 0 -8px 32px -8px rgb(16 15 13 / 0.22);

  /* ── Touch-target sizes (field/glove use) ─────────────────────── */
  --spacing-touch:     3.5rem;  /* 56px — primary buttons         */
  --spacing-touch-sm:  3rem;    /* 48px — icon buttons, absolute min */
  --spacing-touch-row: 4rem;    /* 64px — list rows, tab bar      */
  --spacing-mic:       6rem;    /* 96px — the mic button          */

  /* ── Fonts ────────────────────────────────────────────────────── */
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

Font pick: **Inter** (or **Geist**) with `font-feature-settings: "tnum" 1, "cv05" 1`.
Both ship a proper tabular figure set and neither has an "AI startup" association.
Avoid Space Grotesk / Outfit — they're the visual signature of the look you're avoiding.
Google Fonts is the one external host allowed in artifacts, if relevant.

### 5.3 Semantic layer — maps onto shadcn/ui's variables (light + dark)

This is the speed hack: shadcn components read `--background`, `--primary`, `--border`
etc., so redefining those makes **every shadcn component adopt the palette for free**,
with zero component edits.

```css
:root {
  --background:            var(--color-tierra-50);
  --foreground:            var(--color-tierra-900);
  --card:                  #FFFFFF;
  --card-foreground:       var(--color-tierra-900);
  --popover:               #FFFFFF;
  --popover-foreground:    var(--color-tierra-900);
  --primary:               var(--color-brote-500);
  --primary-foreground:    var(--color-tierra-50);
  --secondary:             var(--color-tierra-100);
  --secondary-foreground:  var(--color-tierra-800);
  --muted:                 var(--color-tierra-100);
  --muted-foreground:      var(--color-tierra-600);   /* 7:1 — sunlight-safe */
  --accent:                var(--color-cielo-50);
  --accent-foreground:     var(--color-cielo-700);
  --destructive:           var(--color-ladrillo-500);
  --destructive-foreground:var(--color-tierra-50);
  --border:                var(--color-tierra-200);
  --input:                 var(--color-tierra-300);
  --ring:                  var(--color-brote-400);
  --radius:                var(--radius-md);

  /* ── Epistemic-status semantics (the §0 idea, as tokens) ──────── */
  --ai:            var(--color-cielo-500);   /* machine said this   */
  --ai-bg:         var(--color-cielo-50);
  --confirmed:     var(--color-brote-500);   /* human confirmed     */
  --confirmed-bg:  var(--color-brote-50);
  --uncertain:     var(--color-ocre-500);    /* needs a human       */
  --uncertain-bg:  var(--color-ocre-50);
  --anomaly:       var(--color-ladrillo-500);/* something is wrong  */
  --anomaly-bg:    var(--color-ladrillo-50);
}

:root:not([data-theme="light"]) { }  /* keep light as default outdoors */

.dark, :root[data-theme="dark"] {
  --background:            var(--color-tierra-950);
  --foreground:            var(--color-tierra-100);
  --card:                  var(--color-tierra-900);
  --card-foreground:       var(--color-tierra-100);
  --popover:               var(--color-tierra-900);
  --popover-foreground:    var(--color-tierra-100);
  --primary:               var(--color-brote-400);   /* lift for contrast */
  --primary-foreground:    var(--color-tierra-950);
  --secondary:             var(--color-tierra-800);
  --secondary-foreground:  var(--color-tierra-100);
  --muted:                 var(--color-tierra-800);
  --muted-foreground:      var(--color-tierra-400);
  --accent:                var(--color-cielo-900);
  --accent-foreground:     var(--color-cielo-200);
  --destructive:           var(--color-ladrillo-400);
  --border:                var(--color-tierra-700);
  --input:                 var(--color-tierra-700);
  --ring:                  var(--color-brote-400);

  --ai:            var(--color-cielo-300);
  --ai-bg:         var(--color-cielo-900);
  --confirmed:     var(--color-brote-300);
  --confirmed-bg:  var(--color-brote-900);
  --uncertain:     var(--color-ocre-300);
  --uncertain-bg:  #3A2A08;
  --anomaly:       var(--color-ladrillo-300);
  --anomaly-bg:    #3A160E;
}
```

Then expose the semantics as utilities so you can write `text-ai`, `bg-uncertain-bg`:

```css
@theme inline {
  --color-ai:            var(--ai);
  --color-ai-bg:         var(--ai-bg);
  --color-confirmed:     var(--confirmed);
  --color-confirmed-bg:  var(--confirmed-bg);
  --color-uncertain:     var(--uncertain);
  --color-uncertain-bg:  var(--uncertain-bg);
  --color-anomaly:       var(--anomaly);
  --color-anomaly-bg:    var(--anomaly-bg);
}
```

### 5.4 Two texture details worth 3 minutes each

1. **A faint soil-grain background.** An inline SVG `feTurbulence` at 3% opacity over
   `--background`. Kills the flat-Tailwind-default look instantly, costs zero assets,
   survives projection.
2. **`tabular-nums` everywhere numbers appear.** `.num { font-variant-numeric:
   tabular-nums; }` applied to every quantity, lot number, and timestamp. It is the
   difference between "web app" and "operational system."

Do **not** add: gradients on buttons, glassmorphism, glow/neon, animated mesh
backgrounds, or an emoji as a logo.

---

## 6. Projector / demo readability

### 6.1 Recommendation: a phone frame in a fullscreen browser. Not device mirroring.

**Do this:** build the app inside a fixed 390×844 container, centred on a
`--background`-tinted desktop page, with a subtle device bezel and a
`transform: scale(1.35)` wrapper. Run Chrome fullscreen (F11) on the projector.

**Why not the alternatives:**
- **Physical phone mirrored** (scrcpy / AirPlay / QuickTime): highest risk-per-reward
  ratio at a hackathon. Cable/driver/permission failure on an unfamiliar projector setup
  costs you 2 of your 5 minutes, and mirroring often letterboxes to a narrow vertical
  strip that wastes 60% of a 16:9 screen. Also: you can't Cmd-Tab to your code.
- **Chrome DevTools device mode**: renders the viewport *smaller* than native and
  surrounds it with DevTools chrome. Looks like debugging, not a product.
- **A phone frame in the browser**: the mobile-first UX is legible *and* you fill the
  screen *and* you can zoom, and there's no hardware in the loop. It also reads as
  deliberate design work — a bezel is a signal that you thought about the form factor.

One caveat: the mic. `getUserMedia` needs HTTPS or `localhost` — both fine. Use a wired
headset or lav mic if the room is loud; ambient hackathon noise wrecks ASR and a failed
live transcription is the worst possible demo moment. **Have a pre-recorded audio blob
or a `?demo=1` scripted-utterance fallback wired in before you present.**

### 6.2 Concrete frame component

```tsx
// app/page.tsx — projector-friendly phone frame
export default function DemoFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh grid place-items-center bg-tierra-100 p-8
                    [background-image:radial-gradient(circle_at_50%_0%,var(--color-tierra-200),var(--color-tierra-100))]">
      <div className="origin-center scale-100 md:scale-125 lg:scale-[1.35] transition-transform">
        <div className="w-[390px] h-[844px] rounded-[2.5rem] bg-tierra-900 p-[10px]
                        shadow-[0_40px_80px_-20px_rgb(16_15_13/0.45)]">
          <div className="relative w-full h-full rounded-[2rem] overflow-hidden bg-background">
            {/* status bar */}
            <div className="h-11 shrink-0 flex items-center justify-between px-6
                            text-sm font-medium text-foreground num">
              <span>9:41</span><span>▮▮▮ ⌁</span>
            </div>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 6.3 Projector floors

- **Minimum rendered text size after scaling: ~22px effective.** With `scale(1.35)`, a
  17px body renders ~23px. That's why the 17px floor in §2.4 exists — it's doing double
  duty for gloves and for the back row.
- **Contrast ≥7:1** for anything you will *point at* during the demo. Projectors lose
  roughly a stop of contrast, and room lights are usually on.
- **No text below 15px** anywhere on screen. Delete the tiny helper text rather than
  shrink it.
- **Animations: 200–300ms, not 150ms.** Sub-150ms transitions are invisible over a
  projector's latency and refresh. Slow the pending→synced stagger and the card entrance
  deliberately so the audience can actually see them happen.
- **Prefer the light theme on the projector unless the room is dark.** If the room is
  dark and the projector is good, dark mode with the `cielo`/`brote` accents is more
  striking — decide by looking at the room, and ship the toggle so you can.
- Test at 1280×720. Many venue projectors are still 720p and will downscale you.

---

## 7. shadcn/ui mapping + code sketches

### 7.1 Component map

| Flow / element | shadcn/ui primitives | Notes |
|---|---|---|
| Voice record button | *custom* + `Button` sizing tokens | see §7.2; no shadcn equivalent |
| Live/final transcript | `Card` + plain spans | two spans, `isFinal` split (§1.3) |
| **Parsed-fields confirmation** | `Card`, `Separator`, `Badge`, `Button`, `Drawer` | see §7.3 |
| Edit one field | `Drawer` (bottom sheet) + `RadioGroup` or `Command` | constrained options, never a text input |
| Clarifying question chips | `Badge` w/ `asChild` on a `button`, or `ToggleGroup` | 2–3 options max |
| Stock dashboard (4 locations) | `Card` grid + `Table` (or `Data Table`) | on mobile use stacked `Card`s, not a table |
| Location detail | `Tabs` or `Accordion` | one tab per location |
| Discrepancy alert | `Card` + `Separator` + `Badge` + `Button` grid | see §4; `Alert` is too small for this |
| Sync-status badge | `Badge` (`variant="outline"` for pending) | see §7.4 |
| Connectivity chip | `Badge` + a `Switch` for the dev offline toggle | |
| Movements feed | `Card` list + `ScrollArea` | `min-h-16` rows |
| Toasts | `Toast` / `Sonner` | `richColors`, bottom position (thumb zone) |
| Loading | `Skeleton` (not `Spinner`) | skeletons for the dashboard, staged labels for the parse |
| Empty states | `Empty` | one line + the mic CTA |

([shadcn/ui component index](https://ui.shadcn.com/docs/components))

**Speed notes.**
- `npx shadcn@latest add card badge button drawer separator table tabs skeleton sonner
  radio-group scroll-area switch empty` — one command, then never touch the generated
  files; theme entirely through §5.3.
- **Charts:** you almost certainly don't need one. A big `--text-2xl` number with a
  `tabular-nums` delta beats a chart for stock levels and costs 1/10th the time. If you
  do want one, shadcn's `Chart` wraps Recharts and inherits `--chart-1..5` — define
  those from the palette.
- **Icons:** `lucide-react` (ships with shadcn). Exact set you need: `Mic`, `Square`,
  `Check`, `ChevronRight`, `AlertTriangle`, `Clock`, `CloudOff`, `RefreshCw`, `Search`,
  `Sparkles`, `MapPin`, `Package`.
- **Animation:** `tw-animate-css` (shadcn's default in v4) covers the pulse and slide-in
  you need. Don't install Framer Motion for three transitions.
- **Fake backend:** Zustand + a seed JSON of 4 locations / ~12 lots. Spend the saved
  time on the parse quality and the two hero cards.

### 7.2 Voice record button with live waveform

```tsx
"use client";
import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";

const BARS = 28;

export function VoiceButton({ onResult }: { onResult: (audio: Blob) => void }) {
  const [state, setState] = useState<"idle" | "rec">("idle");
  const [levels, setLevels] = useState<number[]>(Array(BARS).fill(0.06));
  const [secs, setSecs] = useState(0);
  const ref = useRef<{
    ctx?: AudioContext; stream?: MediaStream;
    rec?: MediaRecorder; raf?: number; chunks: Blob[];
  }>({ chunks: [] });

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;                       // → 32 bins, ~BARS
    ctx.createMediaStreamSource(stream).connect(analyser);

    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(data);
      // mirror around centre so the visualiser reads as symmetric
      const half = Array.from(data.slice(0, BARS / 2), v =>
        Math.max(0.06, Math.min(1, (v / 255) ** 0.7 * 1.6)));
      setLevels([...half.slice().reverse(), ...half]);
      ref.current.raf = requestAnimationFrame(tick);
    };
    tick();

    const rec = new MediaRecorder(stream);
    ref.current.chunks = [];
    rec.ondataavailable = e => ref.current.chunks.push(e.data);
    rec.onstop = () => onResult(new Blob(ref.current.chunks, { type: "audio/webm" }));
    rec.start();

    ref.current = { ...ref.current, ctx, stream, rec };
    navigator.vibrate?.(15);
    setState("rec"); setSecs(0);
  }

  function stop() {
    const r = ref.current;
    r.rec?.stop(); r.stream?.getTracks().forEach(t => t.stop());
    r.ctx?.close(); if (r.raf) cancelAnimationFrame(r.raf);
    setLevels(Array(BARS).fill(0.06));
    navigator.vibrate?.([10, 40, 10]);
    setState("idle");
  }

  useEffect(() => {
    if (state !== "rec") return;
    const id = setInterval(() => setSecs(s => s + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  const rec = state === "rec";
  return (
    <div className="flex flex-col items-center gap-5 pb-8">
      {/* amplitude bars — always mounted so height animates from flat */}
      <div className="flex items-center justify-center gap-[3px] h-16 w-full max-w-[280px]">
        {levels.map((v, i) => (
          <div key={i}
            className={`w-[5px] rounded-full transition-[height] duration-75 ease-out
                        ${rec ? "bg-ladrillo-400" : "bg-tierra-300"}`}
            style={{ height: `${Math.round(v * 64)}px` }} />
        ))}
      </div>

      <button
        onClick={rec ? stop : start}
        aria-label={rec ? "Detener grabación" : "Grabar movimiento"}
        className={`relative grid place-items-center rounded-full
                    size-touch-mic transition-colors duration-200
                    focus-visible:ring-4 focus-visible:ring-ring focus-visible:outline-none
                    ${rec ? "bg-ladrillo-500 text-white"
                          : "bg-tierra-800 text-tierra-50 active:bg-tierra-700"}`}
        style={{ width: "var(--spacing-mic)", height: "var(--spacing-mic)" }}>
        {rec && (
          <span className="absolute inset-0 rounded-full bg-ladrillo-500/30
                           animate-ping motion-reduce:hidden" />
        )}
        {rec ? <Square className="size-8 fill-current" /> : <Mic className="size-9" />}
      </button>

      <p className="text-base font-medium text-muted-foreground num">
        {rec ? `Escuchando… 0:${String(secs).padStart(2, "0")}` : "Tocá para hablar"}
      </p>
    </div>
  );
}
```

### 7.3 Parsed-fields confirmation card

```tsx
"use client";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ChevronRight, AlertTriangle, Check, Sparkles } from "lucide-react";

type Field = {
  key: string; label: string;
  value: string | null;
  sub?: string;                    // resolved-entity enrichment
  confidence: "high" | "low";
  question?: string;               // present iff low + unresolved
  options?: string[];              // chips for the question
};

export function ParsedMovementCard({
  transcript, intent, confidence, fields, note, onConfirm, onEditField,
}: {
  transcript: string; intent: string; confidence: number;
  fields: Field[]; note?: string;
  onConfirm: () => void; onEditField: (key: string) => void;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const open = fields.filter(f => f.question && !answers[f.key]);
  const ready = open.length === 0;

  return (
    <Card className="overflow-hidden rounded-md border-tierra-200 shadow-card
                     animate-in slide-in-from-bottom-4 fade-in duration-300">
      {/* 1 — verbatim transcript, the audit trail */}
      <button className="w-full text-left px-4 py-3 bg-tierra-100/70
                         hover:bg-tierra-200/60 transition-colors">
        <p className="text-sm text-muted-foreground italic leading-snug">
          ❝ {transcript} ❞
        </p>
      </button>
      <Separator />

      {/* 2 — inferred intent + overall confidence */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-label uppercase text-ai flex items-center gap-1.5">
          <Sparkles className="size-3.5" /> {intent}
        </span>
        <Badge variant="outline"
               className="border-ai/40 text-ai num text-sm gap-1.5">
          <span className="size-2 rounded-full bg-ai" />{Math.round(confidence * 100)}%
        </Badge>
      </div>
      <Separator />

      {/* 3 — fields: read-only rows, tap to correct */}
      <dl className="divide-y divide-tierra-200">
        {fields.map(f => {
          const answered = answers[f.key];
          const asking = f.question && !answered;
          return (
            <div key={f.key}
                 className={asking ? "bg-uncertain-bg border-l-4 border-uncertain" : ""}>
              <button onClick={() => !asking && onEditField(f.key)}
                      className="w-full flex items-center gap-3 px-4 text-left
                                 min-h-16 active:bg-tierra-100 transition-colors">
                <dt className="text-label uppercase text-muted-foreground w-24 shrink-0
                               flex items-center gap-1">
                  {asking && <AlertTriangle className="size-3.5 text-uncertain" />}
                  {f.label}
                </dt>
                <dd className="flex-1 min-w-0">
                  {asking ? (
                    <span className="text-base font-medium text-uncertain">{f.question}</span>
                  ) : (
                    <>
                      <span className="block text-lg font-semibold text-foreground num
                                       truncate">{answered ?? f.value}</span>
                      {f.sub && (
                        <span className="block text-sm text-muted-foreground truncate">
                          {f.sub}
                        </span>
                      )}
                    </>
                  )}
                </dd>
                {!asking && <ChevronRight className="size-5 text-tierra-400 shrink-0" />}
              </button>

              {/* clarifying-question chips — one tap, no free text */}
              {asking && (
                <div className="flex flex-wrap gap-2 px-4 pb-4 -mt-1 pl-[7.5rem]">
                  {f.options?.map(o => (
                    <button key={o}
                      onClick={() => setAnswers(a => ({ ...a, [f.key]: o }))}
                      className="h-touch-sm px-4 rounded-sm border-2 border-uncertain/40
                                 bg-background text-base font-medium
                                 active:bg-uncertain-bg transition-colors"
                      style={{ height: "var(--spacing-touch-sm)" }}>
                      {o}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </dl>

      {/* 4 — domain consequence: cheap, high perceived intelligence */}
      {note && (
        <>
          <Separator />
          <p className="px-4 py-3 text-sm text-ocre-700 bg-uncertain-bg
                        flex items-start gap-2">
            <AlertTriangle className="size-4 mt-0.5 shrink-0" />{note}
          </p>
        </>
      )}

      {/* 5 — actions, thumb zone, 56px */}
      <div className="grid grid-cols-[1fr_1.6fr] gap-2 p-3 bg-tierra-50 border-t
                      border-tierra-200">
        <Button variant="outline" className="h-14 text-base">Corregir</Button>
        <Button disabled={!ready} onClick={onConfirm}
                className="h-14 text-base font-semibold gap-2">
          <Check className="size-5" />
          {ready ? "Confirmar" : `Falta ${open.length} dato${open.length > 1 ? "s" : ""}`}
        </Button>
      </div>
    </Card>
  );
}
```

### 7.4 Sync-status badge

```tsx
import { Badge } from "@/components/ui/badge";
import { Check, Clock, RefreshCw } from "lucide-react";

export type SyncState = "pending" | "synced" | "failed";

export function SyncBadge({ state, onRetry }:
  { state: SyncState; onRetry?: () => void }) {
  if (state === "synced") return (
    <Badge className="bg-confirmed-bg text-confirmed border-confirmed/30 gap-1.5
                      text-sm font-medium">
      <Check className="size-3.5" /> Sincronizado
    </Badge>
  );
  if (state === "pending") return (
    <Badge variant="outline"
           className="border-uncertain/50 text-uncertain gap-1.5 text-sm font-medium
                      animate-pulse motion-reduce:animate-none">
      <Clock className="size-3.5" /> Pendiente
    </Badge>
  );
  return (
    <button onClick={onRetry} className="min-h-12 flex items-center"
            style={{ minHeight: "var(--spacing-touch-sm)" }}>
      <Badge className="bg-anomaly-bg text-anomaly border-anomaly/40 gap-1.5
                        text-sm font-medium">
        <RefreshCw className="size-3.5" /> Sin enviar · Reintentar
      </Badge>
    </button>
  );
}
```

---

## 8. Build order under time pressure

Ranked by demo-value per minute. Cut from the bottom.

1. **Tokens (§5.2 + §5.3)** — 10 min, and every subsequent component inherits it.
2. **Parsed-fields confirmation card (§7.3)** — the single most distinctive screen.
3. **Voice button with real amplitude bars (§7.2)** — must be real audio.
4. **Phone frame (§6.2)** — 5 min, transforms how everything else reads on the projector.
5. **Discrepancy card (§4)** — the "wow, it reasons" moment.
6. **Stock dashboard across 4 locations** — big `tabular-nums` numbers, no charts.
7. **Sync badges + offline toggle (§3)** — 15 min for a genuinely memorable beat.
8. Clarifying-question chips (§1.6) — high credibility, low cost; keep if possible.
9. Everything else.

**Demo choreography (5 min).** Dictate a movement live → point at the transcript and the
resolved lot name → answer the one amber question with a tap → Confirmar → flip the
offline switch, dictate a second movement, flip it back and let the badges cascade to
green → open the discrepancy alert, read the hypothesis, tap `Ver en Galpón 2` and land
on the screen that proves it. Close on the epistemic-colour sentence from §0.

---

## Sources

- [WCAG 2.2 — Target Size (Minimum), 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [WCAG 2.2 — Target Size (Enhanced), 2.5.5](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html)
- [web.dev — Offline UX design guidelines](https://web.dev/articles/offline-ux-design-guidelines)
- [MDN — AnalyserNode.getByteFrequencyData](https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/getByteFrequencyData)
- [MDN — MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [MDN — SpeechRecognition (interim results)](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [Tailwind CSS v4 — Theme variables](https://tailwindcss.com/docs/theme)
- [shadcn/ui — Components](https://ui.shadcn.com/docs/components)
- [shadcn/ui — Theming (CSS variables)](https://ui.shadcn.com/docs/theming)
- [Apple HIG — Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility) (44pt minimum tappable area)
- [Material 3 — Accessibility](https://m3.material.io/foundations/accessible-design) (48dp minimum touch target)

Related: [[cursor-hackathon-mar-del-plata-2026]], [[papasud]]
