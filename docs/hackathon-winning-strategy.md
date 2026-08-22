---
tags: [research, hackathon, strategy, papasud]
date: 2026-08-21
event: Cursor Hackathon Mar del Plata 2026-08-22
---

# Winning strategy — Cursor Hackathon Mar del Plata (Papasud challenges)

Event shape: 10:00–16:00, ~3h build, **hard 5-min demo**, in-room judging by organizers + Cursor team + (likely) Papasud people, ~20–30 teams, 9 challenge options (3 verticals × N01–N03), prize $1M ARS funded by a 140-year-old non-tech potato-seed company.

> The single highest-leverage frame: **this is not a scored rubric event, it's a persuasion event in a room.** No published rubric means the decision is made on impression, and the person whose money is on the table is a potato company. Optimize for "the Papasud person in the room says *I want that on Monday*."

Related: [[cursor-hackathon-mar-del-plata-2026]], [[papasud]]

---

## 1. Judging psychology: non-technical sponsor funded the prize AND wrote the problems

**Verdict: "solves the sponsor's actual pain" beats "technically impressive" by a wide margin here.** Three reinforcing reasons:

- **Sponsor-defined challenges → sponsor-round judging.** When a sponsor owns a challenge, the standard pattern is that the challenge owner picks the solution *they are most interested in moving forward with*, not the cleverest build ([MLH Organizer Guide](https://guide.mlh.io/general-information/judging-and-submissions/judges-communication-and-recruiting), [AI Beavers judging guide](https://ai-beavers.com/blog/how-to-judge-hackathon-complete-guide)). Corporate judges score **problem fit, evidence of execution, feasibility, adoption potential, presentation clarity** — note that three of five are non-technical.
- **Missing the stated requirements is instant elimination.** Devpost's judge panel is blunt: projects that miss basic challenge requirements get cut before merit is considered ([Devpost — advice from 5 judges](https://info.devpost.com/blog/hackathon-judging-tips)). So: name the vertical and level explicitly, out loud, on your first slide.
- **Judges reward the "why", not the stack.** "A hackathon project should start with the why"; flashy UIs and "AI-powered" buzzwords get discounted ([JetBrains — Notes From the Judging Table](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)).

### What the Papasud representative specifically responds to
| They respond to | They do not care about |
|---|---|
| Their own vocabulary: *lote, semilla fiscalizada, categoría, bolsón, remito, INASE, trazabilidad, campaña* | Framework choice, architecture, LLM provider |
| A number: "this takes Juan 40 minutes today, this takes 20 seconds" | Latency, token cost, RAG chunking strategy |
| A person by name/role: the field foreman, the warehouse guy at location 3 | "Users" in the abstract |
| Recognising their own real mess on screen (real-looking messy Excel) | A clean synthetic demo dataset |
| Feeling like it could run Monday with their people | Roadmap of 12 future features |
| Spanish. Their whole operation runs in Spanish. | An English-only UI |

**Tactical moves:**
- **Talk to Papasud people during the build window.** They're in the room and they wrote the problems. 15 minutes of interview turns your demo from a guess into "we asked, and Marcelo told us the real bottleneck is X." That sentence is nearly unbeatable in an in-room decision, and no other team will bother. Get one quotable line and one real number from them and put both in the demo.
- **Ask what N03 "advanced" actually meant to them.** The person who wrote the level definitions can tell you which one they'd actually deploy.
- **Credit the sponsor tools out loud.** Explicitly calling out how a sponsor's tool made the project possible is standard advice for sponsor-judged tracks ([DurHack — engaging with sponsors](https://medium.com/@DurHack_press/hacking-your-future-how-to-best-engage-with-sponsors-in-a-hackathon-47423f3959e9)). Here that means **Cursor** (to the Cursor team) and **Wispr Flow** (voice — genuinely relevant to Verticals 2 and 3).

---

## 2. The 5-minute demo

### Hard rules from the sources
- **Show something *working* within ~90 seconds.** "You have to be able to show something working within about 90 seconds" — Jono Bacon ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)).
- **Judges form their opinion in the first 30 seconds** and see dozens of demos ([HackerEarth — 10 tips from 500+ events](https://www.hackerearth.com/blog/10-tips-win-hackathon), [ainna.ai](https://ainna.ai/resources/faq/winning-hackathon-guide)).
- **~30% problem / ~70% solution.** Spend roughly a third of pitch time making the problem land, with a specific persona not a generic category ([AngelHack — what repeat winners do](https://angelhack.com/blog/hackathon-tips-for-winners/), [HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)).
- **One flow, not a feature tour.** "Your demo should be the focus. It should show what your app does in one flow. If it's too long, cut down on your features" — Colin Lowenberg. And: one clear *"oh, this is possible now"* moment outperforms five features — Bonnie Xu ([Devpost](https://info.devpost.com/blog/hackathon-judging-tips)).
- **A confusing demo of a strong project loses to a clear demo of a simpler one** ([Devpost](https://info.devpost.com/blog/hackathon-judging-tips)).
- **Never overrun.** Overrunning reads as not taking it seriously; controlled communication is itself a signal ([Circles.Life — 5-minute pitch](https://medium.com/circleslife/creating-a-5-minute-kickass-hackathon-pitch-17cdcb42c3bc), [TAIKAI](https://taikai.network/en/blog/how-to-create-a-hackathon-pitch)).
- **Live demo, with a recorded fallback.** Live converts far better than video because it's credible and answerable; but record the run twice as insurance ([Guideflow](https://www.guideflow.com/blog/live-demos-vs-recorded-demos), [AngelHack](https://angelhack.com/blog/hackathon-tips-for-winners/)).
- **Talk over the visual — do two things at once.** Narrate the invisible backend while the visible thing happens. Never explain a login screen ([AngelHack — 10 demo tips](https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/)).
- **Guideposts, not a memorized script.** Memorize transitions and the key lines; let the middle fill itself in. Practice **out loud** — "practicing in your head never works" ([AngelHack](https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/)).
- **Be honest about what's mocked.** "Being honest about it reads as confidence" — Avi Press; judges detect missing features anyway ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)).

### Common failure modes to avoid
1. Three of five minutes on context/setup before anything moves on screen.
2. Starting from the tool ("we used Cursor and Exa to…") instead of the pain.
3. No before/after contrast — judges can't size the win.
4. Feature tour: five half-features instead of one complete flow.
5. Live login / live signup / empty-state onboarding shown on stage.
6. A live external API call in the critical path (demo gods).
7. Talking to the screen instead of to the Papasud person.
8. No rehearsal → overrun → cut off mid-punchline.

### 5-minute demo script skeleton (tailored to Papasud)

Write this **before you write code** ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)). One presenter, one driver at the keyboard.

| Time | Beat | Content | Notes |
|---|---|---|---|
| **0:00–0:20** | **Hook — the pain, as a person** | "Marcelo maneja el depósito de [localidad]. Cada mañana pierde 40 minutos cruzando cuatro planillas para saber cuánta semilla tiene. Hoy le vamos a devolver esos 40 minutos." | Name a real person if you interviewed them. No team intro, no "hola somos el equipo…". |
| **0:20–0:40** | **The mess, on screen** | Show the actual ugly Excel / four disconnected sheets for 10 seconds. Say the cost: hours/month, or the discrepancy that cost real money. | This is your credibility slide. Real-looking data > pretty data. |
| **0:40–0:50** | **Name the challenge + the promise** | "Vertical 3, nivel N03. Se llama X. Una frase: hablás, y el stock queda registrado y conciliado en las cuatro plantas." | Explicitly naming vertical + level protects against the "missed requirements" elimination. |
| **0:50–3:20** | **THE DEMO — one happy path, end to end** | Something moves by ~1:00. Do the flow *as the field/warehouse worker would*: on a phone, in Spanish, by voice. Then cut to the manager view where the same event has already landed. Narrate the invisible parts while it runs. | 2.5 min = the bulk. No second flow. No settings screens. If you have a "wow", it lands here around 2:00. |
| **3:20–3:50** | **The wow / the thing they didn't ask for** | One unexpected beat that shows judgment, e.g. the system *flags the discrepancy and proposes a hypothesis* ("faltan 12 bolsones en Planta 2 — coincide con el remito 4471 cargado dos veces"). | This is the line judges repeat to each other afterwards. Pick exactly one. |
| **3:50–4:20** | **Before / after, quantified** | Side-by-side: "Antes: 40 min, 4 planillas, 1 persona. Ahora: 20 segundos, desde el campo, sin escribir." Plus honesty beat: "los datos son una muestra real de 20 años; la integración con [sistema] está mockeada." | The honesty line *increases* trust. Say it fast and move on. |
| **4:20–4:45** | **Monday-morning viability** | "Corre en el celular que ya tienen, funciona sin señal y sincroniza después, y está en castellano. Se puede probar en una planta la semana que viene." | Adoption potential is a scored dimension for corporate judges. |
| **4:45–5:00** | **Tools + close** | "Construido en 3 horas con Cursor — [one concrete Cursor-agent detail]. Voz con Wispr Flow. Gracias." | Credits the two sponsors who matter. End *early*, not late. |

Buffer discipline: rehearse to **4:30**. Live demos always run long.

---

## 3. Difficulty level: N01 vs N02 vs N03

The literature is one-sided on the ambition/polish tradeoff:

- **"The team that ships a working demo of a smaller idea beats the team that demos a broken version of a bigger one."** ([AngelHack](https://angelhack.com/blog/hackathon-tips-for-winners/))
- Judges "don't expect a completely polished, ready-to-go project, but they do look for some degree of polish, thought and effort" ([Eventornado](https://eventornado.com/blog/how-to-judge-a-hackathon-5-criteria-to-pick-winners)).
- Choose a problem that is **finishable, understandable in 30 seconds, and delivers its wow inside one minute** — explicitly "not ambitious" ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)).
- Judges penalize demos that **fail to reach their punchline**, not demos that skip live API calls ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)).
- Counterweight: the Cursor Hamburg winners went at a hard, high-stakes problem — but they won by **stripping every nice-to-have and bulletproofing the single core engine** ([Cursor Forum — 1st place Hamburg](https://forum.cursor.com/t/how-we-built-a-1st-place-ai-digital-guardian-in-48-hours-at-cursor-hackathon-hamburg/150856)).

### Recommendation for 3 hours
**Pick N02, and demo it with N01's reliability.** Rationale:

- N01 in an in-room decision risks reading as "they took the easy one" against 20–30 teams — with no rubric, ambition *is* visible and does count for something.
- N03 in 3 hours almost certainly means a broken or hand-waved demo, which is the one thing judges actively punish.
- **Better play than "attempt N03": ship N02 fully working, then *narrate* the N03 path in 10 seconds** at 4:20 ("el nivel 3 es esto mismo + detección satelital; la arquitectura ya lo contempla, mostramos el mock"). You get credit for the ambition without owning the risk. Frame it as a deliberate engineering decision, not a shortfall.
- If you *do* reach for N03, obey the Hamburg rule: one engine, bulletproof, everything else deleted.

---

## 4. Scope control in ~3 hours

**Timeline (build window ~11:00–15:00 with the demo script written first):**

| Clock | Do |
|---|---|
| First 15 min | Write the 5-min demo script + choose vertical/level. No code. Talk to a Papasud person. |
| First 25% (~45 min) | **End-to-end embarrassing skeleton deployed.** Ugly, hardcoded, but the whole path runs. "The skeleton will look embarrassing. It is supposed to." ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)) |
| Middle 50% | Only the demo-path features. Every ticket must map to a line in the script. |
| Last 25% (~45 min) | **Code freeze.** Polish, seed data, record the fallback video twice, walk the live run 5×. No new features. ([AngelHack](https://angelhack.com/blog/hackathon-tips-for-winners/)) |

**Pre-event tonight (highest ROI hour you have):** repo scaffolded and deployed to Netlify/Render with a hello-world, all API keys in `.env` and verified, Wispr Flow installed and tested, Cursor rules file written with the domain vocabulary, and a seeded fake-Papasud dataset ready. Winners "set up dev environments beforehand, obtain API keys in advance, and write demo scripts before coding" ([AngelHack](https://angelhack.com/blog/hackathon-tips-for-winners/)).

### What to FAKE vs what to BUILD FOR REAL

| Build for real (this is what you're judged on) | Fake / mock / hardcode (nobody cares) |
|---|---|
| The **one core transformation** — voice → structured work order, or question → correct answer over the data | Auth, login, signup, user management (start logged in) |
| The moment of insight — the discrepancy hypothesis, the anomaly flag | Multi-tenant, roles, permissions |
| The mobile/field UI on the actual happy path | Any screen not in the script (settings, profile, history) |
| Spanish-language copy on visible screens | Real ERP / accounting integration → mock adapter with a real-looking payload |
| The seeded dataset's *realism* (messy columns, Spanish headers, 20 years of campaigns) | Satellite/ML anomaly detection → precomputed result on a fixed lote |
| One LLM call that reliably works, with **structured output forced** (schema-constrained JSON, as the Hamburg winners did) | Latency: cache/pre-warm the response; "mock slow API calls" ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)) |
| Deployed public URL (so it's real, not localhost) | Error handling, edge cases, empty states, tests |
| | Live scraping/search in the critical path — pre-fetch Exa/Firecrawl results to a JSON file |

**How to be honest without losing credibility:** one sentence, active voice, framed as a *scoping decision*: "En 3 horas priorizamos el flujo completo de campo a depósito; la integración con el sistema contable está mockeada con un payload real." Then immediately continue. Do **not** apologize, do not list everything that's missing, and never let a judge discover a fake before you name it.

**Also:** write the differentiated logic yourself even if Cursor writes the rest — judges ask about the novel part in Q&A and you must explain it credibly ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon), [AngelHack](https://angelhack.com/blog/hackathon-tips-for-winners/)).

---

## 5. Differentiation bets (20–30 teams, 9 challenges)

### Predicted crowding
- **Vertical 1 (chat + dashboard over 20 years of Excel): heavily crowded — expect 50–70% of teams.** It's the obvious pick: it's the default AI-app shape, it's fully buildable in 3 hours with any RAG/text-to-SQL template, and it needs no hardware or voice. **Expect 10–20 near-identical "chat with your spreadsheet" demos.** By demo #8 the judges are numb. The marginal value of being the 12th chatbot is near zero.
- **Vertical 2 ("smart field": voice work orders, crop photo recognition, satellite anomalies): least attempted.** It's intimidating (vision, satellite, mobile) and looks like it needs field data. **This is the strategic gap.**
- **Vertical 3 (stock/traceability/compliance across 4 locations): moderately attempted, and the most *commercially* legible to Papasud.** Discrepancy hypotheses and export documentation are painful, expensive, audited problems. Voice stock logging is the sub-problem with the best demo-to-effort ratio in the whole event.

### The bets, ranked

1. **Bet A (recommended): Vertical 3, N02 — voice stock logging + unified real-time view with discrepancy hypotheses.**
   Why: under-crowded relative to V1; the demo has *motion and a punchline* (speak → stock updates in 4 locations → system flags and explains a mismatch); it's the problem with the clearest money attached; and Wispr Flow makes voice a sponsor-aligned, 20-minute integration. The discrepancy-hypothesis moment is a natural "wow" no chatbot can match.

2. **Bet B: Vertical 2, N02 — voice-to-structured work order, mobile-first, offline-tolerant.**
   Why: emptiest vertical. Highest "nobody else did this" value. The visual of a phone held up, someone speaking in Spanish over imagined tractor noise, and a structured orden de trabajo materializing is the most physically memorable thing that will happen in that room. Risk: demoing a phone on stage (see §7).

3. **Bet C (only if you want V1): Vertical 1 but explicitly counter-positioned.**
   If you go V1, you must beat 15 chatbots. The differentiators that work: (a) don't show a chat box first — show a *proactive* insight the system found unprompted; (b) answer a question Papasud actually asked you during the build; (c) show the citation back to the exact row in the exact 2011 spreadsheet (trust is the real blocker for a 140-year-old family firm); (d) skip the generic dashboard.

### Cross-cutting differentiators (cheap, high impact)
- **Spanish, throughout.** UI, voice, output. Most teams will build in English out of habit. Their entire operation is in Spanish. This is nearly free and reads as respect.
- **Mobile-first framing for field workers.** A dashboard says "for the office". A phone says "for the 90% of your people who are outdoors". Even a responsive web app in a phone frame wins this framing.
- **Real-data credibility.** Ask Papasud for a real (or realistically messy) file. Demoing on their mess beats demoing on your clean seed data.
- **Domain vocabulary.** Use their words on screen and out loud. Feed them to Cursor as a rules file so the generated UI speaks correctly.
- **Offline tolerance** as a one-line claim: fields have no signal. Say it. It's a detail only someone who thought about *their* reality would mention.
- **Name it something Argentine and memorable**, not "AgroAI Platform".

---

## 6. Cursor-sponsored hackathons specifically

- **Cursor's own judging language across events is design- and story-weighted, not architecture-weighted.** The Cursor × Anthropic Malaysia event judged on exactly three axes: **Innovation** ("creativity and memorability"), **Vision & Delivery** ("how effectively you brought your idea to life"), **Refinement** ("user experience, design quality, attention to detail") ([Cursor × Anthropic Hackathon Malaysia](https://cursor-hack-my.devpost.com/)). "Memorability" and "refinement" are literally named. Other Cursor events have weighted **Visuals & UX Design (20 pts)** on par with **Functionality & Technical Depth (20 pts)**, with **bonus points for exceptional prompt engineering in Cursor**.
- **Implication: UX polish is not a tiebreaker at a Cursor event, it's a primary axis.** Budget real time for it — a clean font, consistent spacing, one accent color, no default-Bootstrap look. This is also where Cursor itself is fastest, so it's cheap.
- **Showing your Cursor process can earn explicit credit.** Where bonus points exist, they're for prompt engineering / creative agent use. Have one 10-second artifact ready: your rules file, or "we ran 3 parallel agents — one on the voice pipeline, one on the sync layer, one on the UI." The Hamburg winner's account emphasizes exactly this: **Agent mode for the hard logic and rapid pivots, 2–5 parallel Cursor conversations on independent parts of the app** ([Cursor Forum — Hamburg 1st place](https://forum.cursor.com/t/how-we-built-a-1st-place-ai-digital-guardian-in-48-hours-at-cursor-hackathon-hamburg/150856)).
- **Cursor events reward "shipped and demoable" over ambitious-and-broken** — multiple Cursor event pages state that only what can be shipped and demoed in the window counts.
- **The Hamburg pattern worth copying:** a serious human problem + one bulletproofed core engine + schema-forced LLM output (Pydantic/Instructor-style constrained JSON with a tiny fixed action set) so there's no parsing flakiness on stage. That last trick is directly applicable to voice → structured work order / stock movement.
- The Cursor team in the room are builders: they will notice a real deployed URL, a fast interaction, and an honest "this part is mocked". They will not be impressed by a slide deck.

---

## 7. Demo-day logistics risk mitigation

Sources agree the demo must be **defensive by design**: Wi-Fi drops, APIs rate-limit, models time out — so mock external services, cache responses, keep screenshots as fallback ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/), [HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon)). Hackathon venue Wi-Fi failing is a normal event, not an edge case ([AngelHack — organizing](https://angelhack.com/blog/how-to-organize-a-hackathon/), [Medium — 36h hackathon with no internet](https://medium.com/ctrlaltgrow/36-hours-hackathon-with-no-internet-no-sleep-and-lots-of-chaos-403d3bcf32f7)).

### Pre-event checklist (tonight)
- [ ] Repo scaffolded, deployed once to Netlify/Render, URL confirmed working from a phone on mobile data.
- [ ] All API keys in place and each one called successfully at least once.
- [ ] Wispr Flow installed, permissions granted, tested with Spanish audio.
- [ ] Cursor rules file with Papasud domain vocabulary.
- [ ] Seeded realistic dataset committed to the repo.
- [ ] Laptop charger + a second charger. Phone charged to 100%.
- [ ] Phone hotspot tested from the laptop, data plan confirmed non-zero.
- [ ] Screen resolution/display scaling set so text is readable on a projector (test at 1280×720 or 1920×1080, bump font sizes).
- [ ] Know the venue's projector connector; bring **HDMI + USB-C→HDMI adapter**.

### 45 minutes before demo (code freeze)
- [ ] **Record the full happy path as a screen-capture video, twice.** Store it *locally* on the laptop (not Drive/YouTube). This is the nuclear fallback.
- [ ] Take **still screenshots of the 5 key screens**, in a local folder, in order — the fallback to the fallback.
- [ ] Walk the live run **5 times**, deliberately hunting for where it breaks.
- [ ] Pre-warm: run the demo path once immediately before going on stage so caches/cold starts are hot.
- [ ] Open every tab you need, logged in, in the right order. Close everything else. Notifications off, Do Not Disturb on, Slack/WhatsApp quit.
- [ ] Bookmark the deployed URL; also have `localhost` running in parallel as a second tab in case the host is down.
- [ ] Battery: plugged in, or ≥80%.

### Phone / mobile-first demo (if you take Bet A or B)
Highest-risk setup in the room. Options, best first:
1. **Best: run the mobile UI in a desktop browser sized to a phone viewport** (DevTools device mode or a CSS phone frame). Zero mirroring risk, still reads as mobile, projector-legible. Do the voice input through the laptop mic.
2. **Second: a teammate holds the real phone while you narrate**, and the laptop shows the manager/dashboard view updating live. This gets you the physical "field worker" theater *and* keeps the projector on a stable machine. Rehearse the handoff.
3. **Avoid: mirroring the phone to the projector live** (scrcpy / AirPlay / QuickTime capture). If you must, test it in the actual room in advance and have option 1 ready as a one-keystroke fallback.
4. **Voice on stage:** the room will be noisy and 100 people will hear you. Test at speaking volume with background noise. Have a **typed-text fallback path** that produces the identical result, so if the mic fails you type the sentence and keep going without breaking stride.

### Connectivity
- [ ] Assume the Wi-Fi dies. **Phone hotspot ready and already paired** — switch in <10 seconds.
- [ ] No live external API in the critical path. Pre-fetched Exa/Firecrawl results as local JSON.
- [ ] If one LLM call must be live, wrap it with a timeout and a cached canned response so it *always* returns something on time.
- [ ] Local-first: the app should render the seeded state with zero network.

### In-room behavior
- [ ] Rehearse to **4:30**, not 5:00.
- [ ] One person talks, one person drives. Never both talking.
- [ ] **If something breaks: do not debug on stage.** Say one calm line ("se cayó la conexión, les muestro la grabación"), switch to the local video, keep the narrative going. Judges remember the overall impression, not the hiccup.
- [ ] Talk to the Papasud person's face, not the screen.
- [ ] Prepare answers to the 4 questions you will be asked: *How long to make this real? How much does it cost to run? Does it work without signal? Who at Papasud uses this first?* Have a crisp answer to each ([AngelHack demo tips](https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/)).

---

## Sources

- [JetBrains — How to Win a Hackathon: Notes From the Judging Table](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)
- [Devpost — How to win a hackathon: advice from 5 seasoned judges](https://info.devpost.com/blog/hackathon-judging-tips)
- [AngelHack — Hackathon Tips: What Repeat Winners Do Differently](https://angelhack.com/blog/hackathon-tips-for-winners/)
- [AngelHack — 10 Tips To Help You Rock Your Next Hackathon Demo](https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/)
- [HackerEarth — How to Win a Hackathon: 10 Tips From 500+ Events](https://www.hackerearth.com/blog/10-tips-win-hackathon)
- [ainna.ai — How to Win a Hackathon: The Method, Not the Tips](https://ainna.ai/resources/faq/winning-hackathon-guide)
- [Cursor Forum — How we built a 1st Place AI "Digital Guardian" (Cursor Hackathon Hamburg)](https://forum.cursor.com/t/how-we-built-a-1st-place-ai-digital-guardian-in-48-hours-at-cursor-hackathon-hamburg/150856)
- [Cursor × Anthropic Hackathon Malaysia — judging criteria](https://cursor-hack-my.devpost.com/)
- [Cursor Hackathon Toronto Tech Week](https://cursor-hackathon-ttw.devpost.com/)
- [Cursor Hackathon: A Reflection — Binh's Newsletter](https://nvbinh.substack.com/p/cursor-hackathon-a-reflection)
- [MLH Organizer Guide — Judges Communication and Recruiting](https://guide.mlh.io/general-information/judging-and-submissions/judges-communication-and-recruiting)
- [AI Beavers — How to judge a hackathon: the complete guide](https://ai-beavers.com/blog/how-to-judge-hackathon-complete-guide)
- [Eventornado — How to judge a hackathon: 5 criteria to pick winners](https://eventornado.com/blog/how-to-judge-a-hackathon-5-criteria-to-pick-winners)
- [DurHack — How to Best Engage with Sponsors in a Hackathon](https://medium.com/@DurHack_press/hacking-your-future-how-to-best-engage-with-sponsors-in-a-hackathon-47423f3959e9)
- [Circles.Life — Creating A 5-Minute Kickass Hackathon Pitch](https://medium.com/circleslife/creating-a-5-minute-kickass-hackathon-pitch-17cdcb42c3bc)
- [TAIKAI — How to Create a Winning Hackathon Pitch in 5 Steps](https://taikai.network/en/blog/how-to-create-a-hackathon-pitch)
- [Guideflow — Live demos vs recorded demos](https://www.guideflow.com/blog/live-demos-vs-recorded-demos)
- [Devpost — 6 Tips for making a winning hackathon demo video](https://info.devpost.com/blog/6-tips-for-making-a-hackathon-demo-video)
- [BizThon — Pitch Perfect: How to Present Your Hack Like a Pro](https://medium.com/@BizthonOfficial/pitch-perfect-how-to-present-your-hack-like-a-pro-1104430a5d93)
- [AngelHack — How To Organize A Hackathon (Wi-Fi contingency)](https://angelhack.com/blog/how-to-organize-a-hackathon/)
- [Medium — 36 Hours Hackathon With No Internet](https://medium.com/ctrlaltgrow/36-hours-hackathon-with-no-internet-no-sleep-and-lots-of-chaos-403d3bcf32f7)
