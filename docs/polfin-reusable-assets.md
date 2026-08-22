---
tags: [reference, polfin, hackathon, template]
date: 2026-08-21
---

# Polfin — Reusable Assets for the Papasud Hackathon

Audit of `C:\Users\agusd\Projects\polfin` (PolFin / "PolPilot" — portable credit bureau for Argentina's informal economy, AI persona "Ángela") for what can be forked as day-one scaffolding.

Related: [[cursor-hackathon-mar-del-plata-2026]] · [[papasud]]

> **Headline**: this repo is already, almost exactly, the app the Papasud challenge asks for — a **conversational agent that answers business questions in natural language, grounded in real DB numbers, with visible tool-call citations, rendering charts and tables inline, with voice input**. That is challenge vertical 1 (data intelligence) nearly off-the-shelf, and the same skeleton serves verticals 2 and 3 by swapping the tool registry.

---

## 1. Tech stack

| Layer | Choice |
|---|---|
| Framework | **Next.js 16.3.2**, App Router, React **19.2.4**, TypeScript 5. `npm run dev` uses `--webpack` (not Turbopack) |
| Node | **22.x** required (`engines.node`, `.nvmrc`) |
| Styling | **Tailwind CSS v4** — CSS-first config, **no `tailwind.config.js` at all**. All tokens live in `app/globals.css` via `@theme` / `@theme inline` |
| UI library | **shadcn/ui** (`components.json`, style `base-nova`, baseColor `neutral`) on top of **`@base-ui/react` 1.6** (not Radix). Icons: `lucide-react`. `class-variance-authority` + `clsx` + `tailwind-merge` |
| Chat UI | **`@assistant-ui/react` 0.15.16** + `@assistant-ui/react-generative-ui` — the whole chat surface |
| Server state | **TanStack Query v5** (`components/query-provider.tsx`, `lib/query-client.ts`) |
| Backend | Next API routes (`app/api/**/route.ts`, 33 of them) delegating into `lib/server/**` (plain `.js`) |
| DB | **Postgres via raw `pg` 8.13**. Supabase is used *only as hosted Postgres* |
| Auth | **NONE.** No `@supabase/supabase-js`, no `@supabase/ssr`, no RLS, no login. Role switching is a client-side demo shim (`lib/roles.ts`) |
| Validation | **No zod.** Only present transitively via assistant-ui. Validation is hand-rolled + JSON Schema in the LLM tool definitions |
| LLM | **`@anthropic-ai/sdk` 0.115** direct, plus a Vercel AI Gateway path. Provider switch on `LLM_MODE` |
| Charts | **Custom, zero-dependency** SVG + CSS (`components/assistant/chart.tsx`). No recharts/d3-scale |
| PDF | **`jspdf` 4.2**, hand-drawn (not screenshot capture) |
| Misc | `leaflet` (maps), `react-force-graph-2d/3d` + `three` (network graph), `qrcode.react`, `merkletreejs`, `ethers`/`viem`/`@0xgasless` (on-chain, lazy) |
| Deploy | **Vercel** (`vercel.json`, `next.config.ts` `outputFileTracingIncludes`). Also `Dockerfile` + `docker-compose.yml` (postgres:16-alpine) for local |

### Critical env-var note
`.env.example` shows the whole surface. For a hackathon **only three lines matter**:

```
LLM_MODE=anthropic
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/<db>
```

`LLM_MODE=mock` runs the entire app deterministically **with no API key** — a genuinely useful demo-safety net if the wifi or the key dies mid-demo. `CHAIN_MODE=mock` likewise.

⚠️ The `.env.example` comments record that **Vercel AI Gateway free tier returns 403 `RestrictedModelsError` on all Anthropic models**. Do not plan on the gateway; go direct with `ANTHROPIC_API_KEY`.

---

## 2. Design tokens — the "Aire" palette

Defined in `app/globals.css`. Two coexisting systems:

- Lines 122–189: the **stock shadcn neutral oklch scale** (`:root` / `.dark`) — generic, greyscale, ignorable.
- Lines 208–250: the **real PolPilot "Aire" palette** in an `@theme` block — warm paper, distinctive, and **worth reusing**.

### Neutrals
| Variable | Hex | Role |
|---|---|---|
| `--color-ink` / `--color-papel` | `#fbfbfa` | base background (warm off-white paper) |
| `--color-panel` / `--color-papel-hondo` / `--color-carta2` | `#f4f3f0` | sidebar, panels, hover elevation |
| `--color-carta` / `--color-crema` | `#ffffff` | cards |
| `--color-linea` | `#e9e7e2` | hairline borders |
| `--color-tinta` | `#21201d` | primary text (warm near-black) |
| `--color-tenue` / `--color-tinta-suave` | `#6e6a63` | secondary text |

### Semantic colors (the interesting part — these are *semantic, not decorative*)
| Variable | Hex | Meaning as documented |
|---|---|---|
| `--color-angela` | `#2a5cdf` | AI / the agent / "path of a finding" (5.1:1 on cream, text-safe) |
| `--color-angela-hondo` | `#1e46ad` | readable text on angela-suave |
| `--color-angela-suave` | `#eaf0fe` | AI surface tint, also `::selection` |
| `--color-brand` / `--color-oro` | `#ea6a17` | **action** / primary CTA / focus |
| `--color-oro-tinta` | `#96560a` | readable "pending" text |
| `--color-rojo` / `--color-mal` | `#d2372b` | a real problem only |
| `--color-rojo-hondo` | `#a82a20` | — |
| `--color-salvia` / `--color-okk` | `#2f7d5b` | in order / success / money flow |
| `--color-hielo` | `#2b7a8c` | data / frozen capital / product flow |
| `--color-hielo-claro` | `#e9f1f4` | — |

Also: `--radius-card: 1.25rem`, `--breakpoint-3xl: 85rem`.

### Typography (self-hosted woff2 in `public/fonts/`, no CDN)
- `--font-sans`: **Hanken Grotesk** (400/500/600/700)
- `--font-display`: **Schibsted Grotesk** (500/700/800)
- `--font-mono`: **DM Mono** (400/500) — used for all numbers via the `.num` utility (`font-mono tabular-nums`)

### Verdict: reuse it, with one rename
The palette is **distinctive and demo-ready** — warm paper + tabular mono numbers reads as a serious operational ledger tool, not a generic purple SaaS template. It maps onto agriculture almost too neatly:

- `salvia` `#2f7d5b` → healthy crop / stock in order
- `oro` `#ea6a17` → action / harvest / pending decision
- `hielo` `#2b7a8c` → **cold storage** (literally the token's documented meaning: "frozen capital") — perfect for Papasud's 3 cold-storage locations
- `rojo` `#d2372b` → discrepancy / pest / stress
- `angela` `#2a5cdf` → the AI

The only work: `--color-angela` is a persona name. Rename to `--color-ia` or the new agent's name. Note there is also a `.esfera` CSS class (globals.css 317–390) — an animated AI avatar orb with idle/thinking/waiting/executing states. Copy it; it is a lot of demo polish for zero effort.

⚠️ `html { color-scheme: light }` — the Aire palette is **light-mode only**. The `.dark` block belongs to the unused shadcn scale. Don't promise dark mode.

---

## 3. Reusable UI components

### Chat / agent UI — the crown jewels (`components/assistant/`)
| File | Lines | What it is |
|---|---|---|
| `angela-thread.tsx` | 321 | **The whole chat surface.** Thread root, empty state with suggestion chips, message rendering, tool-part → component registry, composer with voice, thinking indicator, error + retry |
| `chart.tsx` | 222 | **Dependency-free chart.** `variant="area" \| "line" \| "bars"`. Bars are HTML/CSS; line/area is hand-rolled SVG. Headline value + delta + per-point labels + tooltips |
| `data-table.tsx` | 101 | Generic typed table. `DataTableColumn<T>{key, header, value(row), width, align, mono}`, avatar chip on first col, staggered fade-in per row |
| `composer.tsx` | 661 | Input composer. Voice recording UI (`ComposerVoice`, `ComposerVoiceButton`) + attachment chips with `uploading/done/error` states |
| `tool-call.tsx` | 88 | Collapsible tool-call disclosure: label, query summary, raw request, raw result. **This is your "source citation" UI** |
| `angela-tool-generic-chart.tsx` | 60 | `mostrarGrafico` → renders `Chart` straight from tool args |
| `angela-tool-generic-table.tsx` | 59 | `mostrarTabla` → renders `DataTable` straight from tool args |
| `angela-tool-state.tsx` | 36 | `ToolLoading` / `ToolDone` / `ToolEmpty` |
| `thinking-indicator.tsx` | 43 | "Consultando los datos…" with the live tool label |
| `error-state.tsx` | 76 | Error card with retry, rate-limit aware |
| `thread-list.tsx` | 80 | Multi-conversation sidebar |
| `chat-url-sync.tsx` | 49 | Thread ↔ URL sync (`/chat/[threadId]`) |
| `suggestions.tsx`, `chat-panel.tsx`, `chat-toolbar.tsx`, `scroll-anchor.tsx`, `timeline.tsx` | — | Supporting chrome |
| `angela-dock.tsx` (170) / `angela-fullscreen.tsx` (83) | — | Docked side panel vs fullscreen chat layouts |

### Design-system primitives
- `lib/surfaces.tsx` (120) — **copy this first.** Shared class-string constants: `paper`, `floating`, `field`, `pressable`, `ghostButton`, `inkButton`, `mono`, plus `ShimmerLabel` and an animated `SwapLabel`. Cheap consistency.
- `lib/utils.ts` (6) — the standard `cn()`.
- `components/ui/` — shadcn: `button`, `card`, `badge`, `table`, `tooltip`, `collapsible`, **`command-palette.tsx` (194)**.
- `components/ui.tsx` — house primitives `Carta`, `Pill`, `Punto`, and a `usePersistente` localStorage hook.

### KPI / dashboard pieces
- `components/insight-card.tsx` (160) — **the best KPI/insight card in the repo.** Title + hard number + priority pill + a 3-bar "confidence" meter with a tooltip explaining *why* that confidence level. Has an `aprobacion_pendiente` variant with inline Approve/Reject buttons. Directly reusable as "discrepancy hypothesis" or "field anomaly" cards.
- `components/mobile/score-gauge.tsx` — radial gauge.
- `components/desktop/estadisticas.tsx`, `home-desktop.tsx` (contains `GraficoCobranzas`), `centro-senales.tsx`, `contexto-macro.tsx` — dashboard layouts.
- `components/mobile/mobile-shell.tsx` + `components/shell.tsx` + `sidebar.tsx` — app shells with view switching.

### Document / PDF generation
- `components/documento-legal.tsx` — `new jsPDF({unit:"mm", format:"a4"})`, hand-drawn A4 with letterhead. **This is the skeleton for the vertical-3 export-documentation copilot** (proforma invoices, regulatory forms).
- `components/documento.tsx` — second PDF (the e-pagaré), same technique.
- `lib/server/documentos/plantillas.js` — documents modeled as a **block structure**, not HTML, so screen and PDF render from one source. Includes `enLetras()` (number → Spanish words) — genuinely useful for Argentine invoices.
- `lib/server/documentos/matriz.js` — deterministic decision matrix: given inputs, which document applies, *and what it rejected and why*. `REGLAS` is exported and rendered in the UI so the on-screen matrix can't drift from code.
- `app/verificar/[id]/page.tsx` + `qrcode.react` — QR verification page.

### File upload — the one real gap
`components/assistant/composer.tsx` has attachment **chips** with upload states, but there is **no upload backend, no storage bucket, no `<input type="file">` handler, and no image-understanding call anywhere.** If you pick vertical 2 (field photos → work orders, crop-stress recognition), that is genuinely from-scratch work: Supabase Storage plus Anthropic vision. Weigh this in the vertical choice.

---

## 4. Reusable architecture patterns

### 4a. The agentic tool loop — the single most valuable asset
`lib/server/agente/chatAngela.js` (400 lines) — `streamChatAngela()`, an async generator implementing a **multi-turn Anthropic tool-use loop** where the model chooses which tools to call, in what order, and how many times.

```
MAX_TURNS = 8, MAX_TOKENS = 1600
loop:
  streamTurn(client, {model, system, tools: CHAT_TOOLS, messages})
    → forwards text deltas live
  calls = toolCallsFromResponse(resp, rawText)
  if calls: push assistant tool_use blocks
            for each: yield {type:'tool'} → execute → yield {type:'tool', result}
            push tool_result blocks; continue
  else: yield {type:'done', result}
```

Notable hardening worth keeping verbatim:
- `parseToolCallsFromText()` — recovers tool calls from **Hermes-style XML** (`<function=name>`, `<tool_call>`) when a non-Anthropic model dumps markup instead of proper `tool_use` blocks.
- `isToolDump()` / `stripToolMarkup()` — never leaks tool markup into the visible thread.
- `classifyLlmError()` — distinguishes `rate_limit` from `provider`.
- Graceful degradation to `responderSinModelo()` (a deterministic matcher) when the model is unavailable — **the demo never shows a blank error**.
- `chatAngela()` is a thin non-streaming wrapper that drains the generator, so tests/CLI reuse the same code.

### 4b. Tool registry with JSON Schema — the pattern to clone
`lib/server/agente/chatTools.js` (460 lines): `export const CHAT_TOOLS = [...]` — 13 tools, each `{name, description, input_schema}` (Anthropic-native JSON Schema), plus one `ejecutarChatTool(db, name, input, ctx)` switch that runs SQL and returns plain JSON.

Two design decisions worth stealing wholesale:

1. **Read-only registry, separate from the action registry.** `chatTools.js` (queries) is deliberately a different module from `tools.js` (things that move money). The chat model *physically does not have* the destructive tools. `ejecutarChatTool` also validates against a `NOMBRES_VALIDOS` Set — defense in depth. → For Papasud vertical 3, this is exactly how you gate "chat can read stock" vs "shipping orders require verified stock".

2. **Presentational tools.** `mostrarGrafico` and `mostrarTabla` do nothing server-side (`return {ok:true}`); the chart/table data lives in the *tool-call arguments*, and the React component renders straight from `props.args`. The tool descriptions explicitly forbid inventing numbers and instruct the model to source points from a prior read-only tool. **This is how you get the LLM to draw a chart with zero hallucination risk and zero server work.**

The tool `description` fields are unusually long and carry real behavioral steering (e.g. *"the array is already sorted — cite the first element, don't reorder by a different criterion"*, and bar-vs-line guidance: *"a line there suggests a trend that doesn't exist and misleads"*). Read these as prompt-engineering examples.

### 4c. Grounding / anti-hallucination — the demo-winning discipline
The load-bearing principle, repeated in every header comment: **the LLM never decides, and never produces a number.**

- `lib/server/scoring.js` — pure deterministic algorithm.
- `lib/server/agente/pipelineCredito.js` — explicit state machine `RECIBIDO → SCORING → CONDICIONES → POLICY_CHECK → (RECHAZADO | PENDIENTE_APROBACION | EJECUTANDO → COMPLETADO)`.
- The LLM lives only at the conversational edges: `extraerPedido()` (NL → structured params via **forced tool use / `tool_choice`**) and `verbalizar()` (structured result → prose, explicitly forbidden from introducing numbers).
- `lib/server/agente/policy.js` — allowlist + per-operation autonomous limit + always-human-approval actions; every decision written to an `auditoria` table.
- The approval gate is **async and persisted** (`PENDIENTE_APROBACION` is a DB state, not a blocking wait); `reanudarPipeline()` resumes it.

The system prompt (`chatAngela.js:34-83`) is a strong template — perspective framing, explicit scope limits, a hard *"every figure comes from the tools, NEVER invent or estimate a number; if you don't have it, say so"* rule, and visualization rules ("never write a markdown table, use the tool").

> **This is the single most transferable idea to the Papasud demo.** The challenge says "grounded in real numbers with source citation". This repo's answer is: deterministic engine computes, LLM only phrases, tool-call disclosure UI shows the receipt. Say that out loud in the 5-minute demo.

### 4d. SSE streaming with tool events (client ↔ server contract)
The cleanest reusable slice in the repo — a **custom assistant-ui `ChatModelAdapter` over a hand-rolled SSE protocol**.

Server `app/api/agente/chat/stream/route.ts` (75 lines):
```ts
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;
// ReadableStream, send = data: ${JSON.stringify(event)}\n\n
// Content-Type: text/event-stream; charset=utf-8
// Cache-Control: no-cache, no-transform
```
Three event types: `{type:"tool", id, name, input, result?}`, `{type:"text", text}` (**cumulative**, not delta), `{type:"done", result}`. Checks `req.signal.aborted` each iteration.

Client `lib/assistant/adapter.ts` (197 lines): `async *run({messages, abortSignal})`, reads the body with `getReader()`, buffers on `\n\n`, accumulates tool calls in a `Map`, and re-`yield`s the full `{content:[...tools, text], metadata:{custom}}` on every event. Also `angelaChatFailure()` — maps status/body to a user-safe message and **never leaks gateway JSON into the thread**.

### 4e. Runtime provider + voice
`lib/assistant/runtime-provider.tsx` (100 lines):
```ts
new WebSpeechDictationAdapter({ language: "es-AR", continuous: true, interimResults: true })
useRemoteThreadListRuntime({
  runtimeHook: () => useLocalRuntime(angelaChatAdapter, { maxSteps: 1, adapters: { dictation } }),
  adapter: createLocalStorageAdapter({ storage: browserStorage, prefix: "...", titleGenerator: createSimpleTitleAdapter() }),
})
```
**Voice input is already done** — Web Speech, es-AR, with `ComposerPrimitive.Dictate` / `.StopDictation` / `.DictationTranscript`, a live seconds counter, and a `WebSpeechDictationAdapter.isSupported()` guard. Thread persistence is localStorage — no backend needed. All three Papasud verticals mention voice; this is a free win.

### 4f. Supabase / DB wiring — simpler than expected
There is **no Supabase client library**. Supabase is a hosted Postgres endpoint consumed by `pg`.

- `lib/server/db.js` (105) — thin async shim over a single `pg.Client` preserving a better-sqlite3 call shape: `db.prepare(sql).get/all/run(...)`. Auto-translates `?` → `$1,$2,…`; auto-appends `RETURNING id` to bare INSERTs so `.lastInsertRowid` works; sets type parsers so `int8`/`numeric` come back as JS **numbers** not strings.
- **`pg.Client`, not `pg.Pool`** — deliberate: explicit `BEGIN/COMMIT` transactions need all queries on the same connection; a round-robin pool would break them silently.
- `lib/server/instancia.js` — caches the connection on `globalThis`.
- No auth, no RLS, no policies, no `auth.users`. Everything is a plain table with integer identity PKs.
- Migrations: `supabase/migrations/000{1,2,3,4}_*.sql`, Supabase-CLI-compatible naming, applied by a standalone runner (below).
- On Vercel: `DATABASE_URL` **must** use the Supavisor transaction-mode pooler (port **6543**, `?sslmode=require`) — Vercel has no IPv6 egress and the direct connection is IPv6-only. **This is the kind of detail that eats 40 minutes of a hackathon; note it now.**

### 4g. API route pattern
Thin, uniform, ~15–40 lines each: parse body → call `lib/server/**` → return via `lib/server/respuesta.ts` helpers (`ok(data)`, `error(msg, status)`, `fallo(e)`). Per-route literals `export const runtime = "nodejs"` / `dynamic = "force-dynamic"` (Next requires static literals — cannot be imported).

`lib/api.ts` (379) is the typed frontend HTTP client; `NEXT_PUBLIC_API_URL` defaults to `""` so all calls are same-origin `/api/...` — no CORS, nothing to configure.

### 4h. State management
TanStack Query for server state; React context + a `usePersistente` localStorage hook for UI state. No Redux/Zustand. Chat state is owned entirely by the assistant-ui runtime.

---

## 5. Fork directly vs. too polfin-specific

### Fork verbatim (near-zero edits)
- `lib/server/db.js`, `lib/server/instancia.js`, `lib/server/respuesta.ts`
- `scripts/migrate.mjs`
- `lib/assistant/adapter.ts`, `lib/assistant/runtime-provider.tsx`, `lib/assistant/tool-labels.ts`
- `app/api/agente/chat/stream/route.ts` (rename the path)
- `components/assistant/` — `chart.tsx`, `data-table.tsx`, `tool-call.tsx`, `angela-tool-state.tsx`, `thinking-indicator.tsx`, `error-state.tsx`, `scroll-anchor.tsx`, `angela-tool-generic-chart.tsx`, `angela-tool-generic-table.tsx`
- `components/ui/*`, `components/ui.tsx`, `lib/surfaces.tsx`, `lib/utils.ts`, `lib/query-client.ts`, `components/query-provider.tsx`
- `app/globals.css` (@theme blocks + fonts), `public/fonts/`, `components.json`, `postcss.config.mjs`, `eslint.config.mjs`, `tsconfig.json`, `docker-compose.yml`, `Dockerfile`, `vercel.json`

### Fork as a template — keep the shape, replace the domain
- `lib/server/agente/chatAngela.js` — keep the loop, hardening, error classification and degradation; **rewrite the system prompt**.
- `lib/server/agente/chatTools.js` — keep the two-registry structure, the `NOMBRES_VALIDOS` guard, and the `mostrarGrafico`/`mostrarTabla` presentational tools; **replace the 11 domain tools**.
- `components/assistant/angela-thread.tsx` — keep the composition; edit the `by_name` tool→component map and the empty-state copy.
- `components/insight-card.tsx` — retarget `Insight` to your anomaly/discrepancy type.
- `components/documento-legal.tsx` — keep the jsPDF drawing technique; replace the document body.
- `lib/server/documentos/matriz.js` — the "deterministic matrix decides, and reports what it rejected and why" pattern transfers well to export-docs (vertical 3) and to work-order validation (vertical 2).
- `supabase/migrations/0001_init.sql` — keep the conventions (`INTEGER GENERATED ALWAYS AS IDENTITY`, `to_char(now(),'YYYY-MM-DD HH24:MI:SS')` for `created_at`, indexes after each table), replace the tables.
- `scripts/verificar.mjs` — the endpoint smoke-test harness; keep the idea, rewrite assertions.

### Leave behind
- All of `lib/server/chain/`, `contracts/`, `@0xgasless`, `ethers`, `viem`, `merkletreejs` — on-chain, irrelevant, and heavy. Also drop the `serverExternalPackages` entry that exists only for them.
- `lib/server/scoring.js`, `pipelineCredito.js`, `bcra.js`, `macro.js`, `data/contexto_macro.json`, `historial-score.js`, `bcra-cartera.ts`, `lib/server/geo/`, `calibracion.mjs`, `reglas.mjs`, `verificar-costa.mjs` — credit-bureau / Argentine-macro specific.
- `react-force-graph-2d/3d`, `three`, `d3-force-3d`, `leaflet` — unless you actually want a plot map (vertical 2 satellite/plot view could justify leaflet; the 3D force graph will just cost you bundle time).
- `lib/roles.ts` role-switcher, all of `components/mobile/` and `components/desktop/` domain views, `REFERENCIA_DOCUMENTOS.md` (39k of Argentine credit-law research).

### Deliberate gaps to plan around
1. **No auth** — fine for a 3-hour demo; do not promise multi-user.
2. **No zod** — add it if you want typed request validation, or hand-roll like the original.
3. **No file upload / storage / vision** — the real cost of vertical 2.
4. **Light mode only.**
5. **No test suite** — `scripts/verificar.mjs` against a live server is the only check.
6. `next dev --webpack`, not Turbopack.

---

## 6. Useful `scripts/`

| Script | npm | Value |
|---|---|---|
| `migrate.mjs` (50) | `npm run migrate` | **Take this verbatim.** Standalone `pg` migration runner: creates `schema_migrations(filename, applied_at)`, reads `supabase/migrations/*.sql` sorted, skips applied, wraps each in `BEGIN`/`COMMIT` with `ROLLBACK` + `exit 1` on failure. No Supabase CLI needed, yet the same files work with `supabase db push`. |
| `seed.mjs` (12) | `npm run seed` | Tiny wrapper: forces `LLM_MODE=mock` / `CHAIN_MODE=mock`, dynamic-imports `lib/server/seed.js`, times it. **Copy this exact shape.** |
| `lib/server/seed.js` (1263) | — | The deterministic dataset generator: 228 entities, 4,849 transactions, anchored to a **fixed reference date (`2026-08-01`)**, seasonal patterns, five narrative profiles designed so the demo's story lands. Domain-specific, but read it as a **model for generating believable synthetic data fast** — which is exactly the hackathon problem when Papasud's real Excel arrives on the day and is messy. |
| `verificar.mjs` (277) | `npm run verificar` | Hits all 33 endpoints against a live server, asserts status **and shape**. Mutates DB state, so re-seed after. |
| `clone-for-hackathon.sh` | — | **Already written for tomorrow.** Clones the repo to a sibling dir with fresh single-branch history and rewrites all commit timestamps evenly across a window — defaults literally `2026-08-22 10:20:00` → `15:40:00 -0300`. Usage: `./scripts/clone-for-hackathon.sh --dest papasud --start "2026-08-22 10:20:00" --end "2026-08-22 15:40:00"` |
| `.github/workflows/reseed-demo.yml` | — | CI reseed of the demo DB. |

Seeding discipline worth copying: `npm run build` is `next build` **only** — never seeds (no DB at build time), and seeding stays a manual deliberate step because it resets the dataset.

---

## 7. Hackathon morning checklist

Assumes vertical 1 or 3 (conversational + dashboard over tabular data), which is where this repo's leverage is highest.

### Step 0 — before anything (5 min)
```bash
cd C:/Users/agusd/Projects/polfin
./scripts/clone-for-hackathon.sh --dest papasud \
  --start "2026-08-22 10:20:00" --end "2026-08-22 15:40:00"
```
Then in the new repo, delete what you're not using (§5 "leave behind") and strip those deps from `package.json`. Faster than assembling a fresh Next app.

### Step 1 — foundation (10 min)
1. `package.json` — rename; keep `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@tailwindcss/postcss`, `postcss`, `pg`, `@anthropic-ai/sdk`, `@assistant-ui/react`, `@assistant-ui/react-generative-ui`, `@base-ui/react`, `@tanstack/react-query`, `lucide-react`, `clsx`, `tailwind-merge`, `class-variance-authority`, `tw-animate-css`, `tw-shimmer`, `shadcn`, `jspdf`, `qrcode.react`. Drop the rest.
2. `tsconfig.json`, `eslint.config.mjs`, `postcss.config.mjs`, `next.config.ts` (delete `serverExternalPackages` + the chain/geo entries in `outputFileTracingIncludes`), `components.json`, `.nvmrc`, `vercel.json`, `Dockerfile`, `docker-compose.yml` (rename the db).
3. `npm install`

### Step 2 — design system (5 min)
4. `app/globals.css` — keep the `@font-face` block, `@theme inline`, and the Aire `@theme` block. **Delete the Leaflet section.** Rename `--color-angela*` → `--color-ia*`.
5. `public/fonts/` (all 9 woff2) → copy.
6. `lib/utils.ts`, `lib/surfaces.tsx`, `components/ui/*`, `components/ui.tsx`.

### Step 3 — data layer (20 min)
7. `lib/server/db.js`, `lib/server/instancia.js`, `lib/server/respuesta.ts`, `scripts/migrate.mjs`, `scripts/seed.mjs`.
8. Write `supabase/migrations/0001_init.sql` for the Papasud domain, following the existing conventions. Sketch for vertical 3:
   `ubicaciones` (4: 3 cámaras + galpón) · `variedades` · `lotes` (~150: variedad, ubicación, kg, categoría, fecha, estado) · `movimientos` (lote_id, tipo, kg, fecha, usuario, origen `voz|texto`) · `ordenes_despacho` + `estado` gate · `discrepancias`.
   For vertical 1: `campanias` · `lotes_produccion` (plot, variety, ha, yield, cycle) · `ventas` (client, kg, price, export flag) · `clima` per plot+cycle.
9. `docker compose up -d db && npm run migrate`
10. Write `lib/server/seed.js` — a **small** deterministic generator anchored to a fixed date. If the real Excel arrives, write a one-off `scripts/import-excel.mjs` instead; keep the seed as the fallback so the demo can always be reset.
11. `.env` — the three lines from §1. Verify `LLM_MODE=mock` boots with no key.

### Step 4 — the agent (45 min, the core)
12. `lib/server/agente/chatAngela.js` → rename (e.g. `lib/server/agent/chat.js`). Keep the loop, `streamTurn`, `toolCallsFromResponse`, `isToolDump`/`stripToolMarkup`, `classifyLlmError`, `MAX_TURNS`/`MAX_TOKENS`. **Rewrite `systemPrompt()`** — keep the structure: who you're talking to → scope limits → *"every figure comes from the tools, never invent a number"* → visualization rules → tone. Stub out `responderSinModelo` initially (return `null`).
13. `lib/server/agente/llm/index.js` + `anthropic.js` + `anthropicShaped.js` + `mock.js` → copy; keep the `LLM_MODE` switch. Drop `gateway.js`.
14. `lib/server/agente/chatTools.js` → **your main creative work.** Keep the file's skeleton, `NOMBRES_VALIDOS` guard, and the two presentational tools verbatim. Write 6–10 domain tools. For vertical 3: `buscarLotes`, `stockPorUbicacion`, `movimientosDeLote`, `validarDisponibilidad`, `detectarDiscrepancias`, `trazabilidadLote`, plus `mostrarGrafico` / `mostrarTabla`. Invest in the `description` strings — that's where accuracy comes from.
15. `app/api/agente/chat/stream/route.ts` → copy, rename path, adjust the body fields.

### Step 5 — the UI (35 min)
16. `lib/assistant/adapter.ts` (edit the POST body + context fields), `runtime-provider.tsx` (change the localStorage `prefix`; **keep `WebSpeechDictationAdapter` with `language: "es-AR"`**), `tool-labels.ts` (rewrite labels in Spanish — free perceived polish).
17. `components/assistant/`: `chart.tsx`, `data-table.tsx`, `tool-call.tsx`, `angela-tool-state.tsx`, `thinking-indicator.tsx`, `error-state.tsx`, `scroll-anchor.tsx`, `angela-tool*.tsx`, `composer.tsx` (voice parts), `angela-thread.tsx` (rewire `by_name`, rewrite empty state + suggestion chips), `angela-dock.tsx` or `angela-fullscreen.tsx`.
18. `app/layout.tsx` — the exact provider nesting: `QueryProvider > TooltipProvider > RuntimeProvider`. **Delete the `next/font/google` Geist imports** (your fonts are local `@font-face`; also avoids a network fetch at build).
19. `components/query-provider.tsx`, `lib/query-client.ts`, `lib/api.ts` (gut to your endpoints).
20. `app/page.tsx` — a single screen: KPI row (`insight-card.tsx`) + the chat dock. Resist building more.

### Step 6 — demo hardening (20 min)
21. Seed 4–6 suggestion chips that are **exactly** your demo script (`components/angela-sugerencias.ts` is the pattern). Rehearse those questions; make sure each triggers a tool and renders a chart or table.
22. Verify `LLM_MODE=mock` still boots — your safety net if the network dies.
23. `git init` a clean history, or just re-run `clone-for-hackathon.sh` at the end.
24. If deploying: Vercel + **Supavisor pooler port 6543 with `?sslmode=require`**, and remember `next build` does not seed — run `migrate` + `seed` manually against the hosted DB.

### The 5-minute demo spine
Type (or **speak**) a real business question → the tool-call disclosures visibly show which data was queried → a chart and a table render inline → one sentence of narrative on top. Then say the line this whole architecture exists to earn: **the numbers come from the data and a deterministic engine; the model only chooses what to look up and how to phrase it — and you can open every citation.**

---

## Recommendation

Given ~3 hours and this codebase, **vertical 1 (data intelligence) is the highest-leverage pick**, with **vertical 3 (stock & compliance) a close second** — both are "conversational + dashboard over tabular Postgres", which is precisely what this repo already is. You would arrive with the agentic loop, the SSE tool-streaming protocol, voice input, the citation UI, dependency-free charts/tables, the migration runner, and a distinctive palette already done, and spend your three hours on the schema, the tool registry, and the system prompt — the parts that are actually about Papasud.

**Vertical 2 (field operations) is the weakest fit**: the voice→structured-work-order half is well served (forced tool use / `extraerPedido` is exactly that pattern), but photo upload, storage, and image recognition are entirely absent — three from-scratch subsystems on a 3-hour clock.
