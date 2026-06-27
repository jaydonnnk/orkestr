# Orkestr — Build Guide v2 (Unified)
### Build2026 · Saturday 27 June · 9:00 AM – 9:00 PM

> **This replaces v1.** v1 described a single scripted demo page. We changed direction:
> we're building the **full 14-screen webapp** — Leeshan's frontend talking to a real
> REST backend. The backend skeleton is already built, runs, and is seeded. This guide
> tells each of you exactly what to do, in which folder, and how.

**What Orkestr is:** the group chat that never resolves — *"where do we eat Friday?" → "idk" → [silence]*. Each person sets their constraints once, the agents negotiate a plan everyone accepts, the Convener books it with the venue's own agent, and the bill settles itself on x402. **Splitwise does the splitting after you decide; Orkestr does the deciding, strikes the booking, and clears the debt.**

---

## 1. How the pieces fit (read this first)

```
  Leeshan's Next.js app  (frontend/)        ← what the user sees · 14 screens · cream/coral
          │
          │  HTTP calls via lib/api.js  (http://localhost:8000)
          ▼
  FastAPI backend  (api/main.py)            ← Lucas runs + owns this
          │
          ▼
  Session store  (core/session.py)          ← the "brain": state per group, seeded ORK-001
          │
          ├─ agents/      ← Jaydon: the Convener negotiates + books
          ├─ core/settlement.py  ← the real debt-simplification (done)
          ├─ payments/    ← x402 + AP2 mocks (done)
          └─ ai/          ← Nigel: the LLM bits
```

**The golden idea: real endpoints, seeded data underneath.** Every screen, route, and API call is real. The negotiation, plan, and settlement come from **seeded session state** (a pre-loaded group called `ORK-001`), so nobody is debugging 5-way live sync at 8pm. You swap stubs for real logic *behind* the API without breaking the frontend. This is what makes "go big" survivable in 10 hours.

**The two artifacts that are the source of truth:**
- Frontend → `docs/ORKESTR_FRONTEND.md` (Leeshan's 14-screen spec, her API wrapper, her design tokens).
- Backend → this guide + the running code. The API contract is in §6 below.

---

## 2. Run the whole thing locally

Two terminals. Backend first.

**Terminal 1 — backend (from the repo root):**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell). Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
Now open `http://localhost:8000/docs` — that's FastAPI's **auto-generated API explorer**. You can click every endpoint and try it live. The seeded group `ORK-001` is already loaded.

**Terminal 2 — frontend:**
```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```
In `frontend/.env.local`: keep `NEXT_PUBLIC_USE_MOCK=true` while building screens; flip to `false` (and set `NEXT_PUBLIC_API_URL=http://localhost:8000`) to connect to the live backend.

**Seeded demo group:** every screen works against session id **`ORK-001`** out of the box — it's pre-loaded with the 5 friends, the Seoul Garden plan, the co-signed booking, the 3 logged expenses, and the 3 pending transfers. Use it for the demo.

---

## 3. Who owns what (stay in your folder)

| Person | Branch | Your folders | One-line job |
|---|---|---|---|
| **Jaydon** | `jaydon` | `agents/`, `core/settlement.py` | The agent brain: how the Convener negotiates + books. Pitch lead from 6pm. |
| **Lucas** | `lucas` | `api/`, `core/session.py`, `payments/` | Owns + runs the backend. The API contract is his to keep stable. |
| **Leeshan** | `leeshan` | `frontend/` (everything) | All 14 screens + the cream/coral theme + the two money-shot animations. |
| **Nigel** | `nigel` | `ai/`, `data/` | The LLM bits + seed data + **demo ops** (the demo route, backup video, QA). |

**Shared files — ping the chat before editing:** `data/personas.json`, `data/venues.json`, `README.md`. Git rules are in `GIT_WORKFLOW.md` — pull before you start, push when you pause.

---

## 4. Per-person playbooks

### 🟧 Jaydon — `agents/` + `core/settlement.py`

**What already works (don't rebuild):** `core/settlement.py` (the real min-cash-flow debt simplification) is done and tested. `agents/convener.py` already returns a perfect seeded 3→1 negotiation. `agents/settlement_agent.py` already calls your real algorithm.

**What you build (in order):**
1. **`agents/persona.py` → `stance(persona, plan)`** — right now it always returns `"accept"`. Make each persona react to the proposed plan using their real constraints: if `plan["day"]` isn't in `persona["constraints"]["available_days"]` → return `stance: "object", constraint_ref: "available_days"`. Same for budget (`per_person > budget_max`) and dietary. This is the engine that makes the ring's objections real instead of scripted.
2. **`agents/convener.py` → `run_negotiation()`** — turn it into real rounds: propose candidate 1 → collect everyone's `stance()` → if any objections, propose candidate 2 → repeat until all accept. **Keep the current seeded version as a fallback** and only switch the live one on once it reliably converges — the seeded narrative is demo-perfect, so don't lose it.
3. **`agents/convener.py` → `generate_candidates()`** — currently one seeded plan. Optionally call Nigel's `ai/plan_gen.generate()` to produce candidates from the freeform prefs. Agree the return shape with Nigel first.

**How to test (no server needed):**
```bash
python -c "import sys; sys.path.insert(0,'.'); from agents.convener import run_negotiation, generate_candidates; import json; p=json.load(open('data/personas.json')); v=json.load(open('data/venues.json')); print(run_negotiation(generate_candidates(p,v), p))"
```
You write the functions; Lucas's endpoints call them. You two meet at the function names in `agents/` — don't change a signature without telling him.

**From 6:00 PM:** hand the backend to Lucas, become pitch lead (§9).

---

### 🟦 Lucas — `api/` + `core/session.py` + `payments/`

**What already works (don't rebuild):** every endpoint in §6 exists and returns the right shapes. `core/session.py` is a working state machine (create → constraints → negotiate → approve → expenses → settle). Seeded `ORK-001` loads on startup. CORS is set for `localhost:3000`.

**Your job is to keep it running and harden it:**
1. **Run the server all day** (`uvicorn api.main:app --reload --port 8000`). You are the integration point — when Leeshan's screen has no data, you check the endpoint at `/docs`.
2. **`core/session.py`** — when Jaydon's real negotiation is ready, it already flows through `compute_plan()`. Your job: handle edge cases (empty members, double-submits, re-approvals) so live demos don't 500.
3. **`api/main.py`** — keep the contract stable for Leeshan. If she finds she needs a field or endpoint, add it here. Don't rename existing ones.
4. **`payments/`** — the x402 + AP2 mocks are done. Stretch: in `payments/mandate.py → verify()`, add the **tampered-cart catch** (return `False` if the cart was altered after signing) — that's a great Act-2 flourish for the trust theme.

**How to test:** open `http://localhost:8000/docs`, click an endpoint, hit "Try it out". Or quick checks:
```bash
curl http://localhost:8000/api/status/ORK-001
curl http://localhost:8000/api/settlement/ORK-001
```

**You and Leeshan share the contract in §6.** When she flips `USE_MOCK=false`, your job is that everything just connects.

---

### 🟪 Leeshan — `frontend/` (your whole app)

**Build from your own guide, `docs/ORKESTR_FRONTEND.md`.** You own all 14 screens, the cream/coral theme (`.cursor/rules/orkestr.mdc`), and the components.

**How to work without waiting on the backend:** build every screen against `lib/mockData.js` first (`USE_MOCK=true`). The mock data matches the live API exactly, so when you flip `USE_MOCK=false` at integration time, screens just connect — nothing else changes.

**Build order (matches the user's journey):**
1. **Phase 1 screens:** create → join (constraints) → waiting → plan → approve → confirmed.
2. **Phase 2 screens:** event → log expense → running tab.
3. **Phase 3 screens:** confirm fronted → who owes what → approve transfer → settled.

**⭐ Your two most important screens — these are the demo's peak, don't treat them as filler:**
- **`/waiting/[id]` — the negotiation ring (Act 1).** Your guide had this as a spinner. Instead, fetch `GET /api/negotiation/[id]` and render the 5 agents in a ring with the objection/accept messages converging 3→1. Animate it (Framer Motion). *This is money shot 1.*
- **`/confirmed/[id]` — the agent handshake (Act 2).** Fetch `GET /api/handshake/[id]` (it returns the full `request → response → mandate`) and show the two agents transacting: your agent asks, the venue's agent counters 7→7:30, they co-sign. *This is money shot 2 — "your agent transacting with theirs."*
- **`/settle/[id]` — the collapse (Act 3).** The tangle of who-owes-whom simplifying to 3 transfers and hitting zero. Framer Motion, the one screen your guide already nailed.

**Reference for the look:** the cream/coral mockup we built — warm cream surfaces, coral for primary actions, amber for money + booking-confirmed. Phone-first (48px tap targets, 16px inputs).

**Test:** `npm run dev`, build against mock, then point at `localhost:8000` and walk the flow for `ORK-001`.

---

### 🟩 Nigel — `ai/` + `data/` + demo ops

**What already works (don't rebuild):** `data/personas.json` and `data/venues.json` are populated and tuned so the demo resolves to Seoul Garden. The seeded settlement already nets to zero.

**What you build:**
1. **`ai/plan_gen.py → generate(personas, venues)`** — the LLM (OpenAI/Codex, credits provided) that reads everyone's freeform note and proposes candidate plans. Evidence-bound: never invent a constraint. Agree the return shape with Jaydon (he calls this from `convener.generate_candidates`). Put `OPENAI_API_KEY` in `.env`.
2. **`ai/narrate.py`** — turn negotiation messages into natural lines, the venue dialogue, and the "Settled" copy. Narrate only the real `constraint_ref`.
3. **`data/`** — own the seed tuning. If the demo needs a sharper objection or a cleaner resolution, you adjust the numbers here (coordinate before editing — it's a shared file).

**Demo ops (this is high-value and blocks nobody):**
- **Design the demo route** (§8) — the curated path through 14 screens that hits all three money shots. You can't put 5 phones in front of judges; you script one path.
- **Record the backup video** of the full run by ~7pm — insurance if the wifi dies on stage.
- **QA** — click through every screen against the live backend, write down anything that breaks, hand the list to Lucas/Leeshan.
- **Cold-open** — mock the dead group chat ("where do we eat??" / "idk anywhere") for slide 1.

**Test:** run `plan_gen` standalone (`python -c "from ai.plan_gen import generate; ..."`); for everything else, you're the one clicking through the real app.

---

## 5. The two money shots (the part that wins)

Everything above is plumbing. **Two screens are why a judge remembers Orkestr**, and both were missing from the original frontend plan — so they get extra attention from Leeshan, and they have dedicated endpoints:

| Beat | Screen | Endpoint | Owner |
|---|---|---|---|
| **Act 1 · agents converge** | `/waiting/[id]` | `GET /api/negotiation/[id]` | Leeshan (viz) · Jaydon (logic) |
| **Act 2 · agent ↔ agent booking** | `/confirmed/[id]` | `GET /api/handshake/[id]` | Leeshan (viz) · Lucas/Jaydon (co-sign) |
| **Act 3 · settlement collapse** | `/settle/[id]` | `GET /api/settlement/[id]` | Leeshan (viz) |

If you're behind on time, cut a Phase-2 screen (the running tab, an expense edit) — **never** cut polish on these three.

---

## 6. API reference (Leeshan ↔ Lucas contract)

All live now. Base: `http://localhost:8000`. Seeded session: `ORK-001`.

| Method | Route | Returns / Body |
|---|---|---|
| POST | `/api/session/start` | `{session_id, invite_url}` |
| POST | `/api/constraints` | body = person shape (`session_id, id, name, constraints, freeform`) |
| GET | `/api/status/{id}` | `{phase}` — `negotiating` → `plan_ready` → `booking` → `confirmed` |
| GET | `/api/negotiation/{id}` | the 3→1 messages **(feeds the ring)** |
| GET | `/api/plan/{id}` | the plan (title, day, time, venue, activity, costs) |
| POST | `/api/approve/{id}` | body `{person_id}` — releases that share |
| GET | `/api/handshake/{id}` | `{request, response, mandate, booking_ref, status, merchant}` **(feeds the handshake)** |
| GET | `/api/expenses/{id}` | logged expenses array |
| POST | `/api/expense/{id}` | body `{paid_by, amount, description, split}` |
| GET | `/api/settlement/{id}` | `{fronted, shares, net, transfers, net_after}` |
| POST | `/api/settle/{id}` | body `{person_id}` to approve a transfer, or `{fronted}` to confirm amounts |

Full request/response examples live in `docs/ORKESTR_FRONTEND.md` §4.

---

## 7. Timeline (hour by hour)

> The skeleton already runs, so we skip scaffolding and go straight to building screens + logic.

| Time | Everyone |
|---|---|
| **9:00–9:30 · Setup** | Clone the repo, run backend + frontend, confirm `ORK-001` renders, claim your branch + folder. Read your playbook (§4). |
| **9:30–11:30 · Phase 1** | **Leeshan:** create → constraints → waiting → plan → approve → confirmed (against mock). **Lucas:** server up, harden session edge cases. **Jaydon:** real `stance()` + negotiation rounds (keep seeded fallback). **Nigel:** `plan_gen` + tune data + draft the demo route. |
| **11:30–1:00 · Phase 2 (+lunch)** | **Leeshan:** event → expense → tab, **and start the ring on `/waiting`**. **Lucas:** wire Jaydon's real negotiation into `session.py` if ready. **Jaydon:** finish negotiation. **Nigel:** `narrate` + cold-open. |
| **1:00–3:00 · Phase 3** | **Leeshan:** confirm → who owes → approve → settled, **+ the handshake on `/confirmed` + the settlement collapse animation**. Others: support + start hardening. |
| **3:00–4:30 · INTEGRATION** | Flip `USE_MOCK=false`. Whole team walks the full flow against the live backend for `ORK-001`. Fix every break. **No new features.** |
| **4:30–6:00 · Demo route + polish** | Nigel + Leeshan nail the curated demo path and the three animations. |
| **6:00–7:30 · Rehearse + backup** | Jaydon → pitch lead, locks the 4-min pitch. Nigel records the backup video. Run it end-to-end repeatedly on the presenting laptop. |
| **7:30–8:30 · Buffer + stretch** | Hold as buffer. If ahead: the tampered-cart catch, or a second seeded group. |
| **8:30–9:00 · Tools down** | Final rehearsal. Present. |

**Milestones:** Phase-1 screens render on mock by 11:30 · full flow works on mock by 3:00 · full flow works on **live backend** by 4:30 · demo route rehearsed by 7:30.

---

## 8. The demo route (a 14-screen app needs a script)

You can't hand judges five phones. Drive **one curated path** on the seeded `ORK-001`, narrating as you go. The route:

1. **Cold open** (slide): the dead group chat. *"Five people, three days, zero decisions."*
2. **`/join/ORK-001`** — set Bob's constraints (10 seconds). Hit "Find our plan."
3. **`/waiting`** — 🎯 the **ring**: five agents arguing, objections resolving, 3→1. *"Watch them argue their way to a plan."*
4. **`/plan`** — the canvas: Seoul Garden, Fri 7:30, $80/person. Tap Approve.
5. **`/confirmed`** — ⭐ the **handshake**: your agent vs the venue's agent, 7→7:30, co-signed. *"The future isn't you transacting with a person — it's your agent transacting with theirs."*
6. **`/settle`** — 🎯 the **collapse**: the tangle simplifies to 3 transfers and hits zero.
7. **`/settle/done`** — "Everyone's square." *"Nobody decided. Nobody chased. It just happened."*

Nigel owns rehearsing this until it's muscle memory. Skip the create/invite/tab screens in the live run — mention them, don't click them.

---

## 9. Pitch (Jaydon, 4 min) + armed answers

**Arc:** the pain (coordination is a tax nobody solves; someone always eats the cost) → the shift (*your agent transacting with theirs*) → **the demo route** → why it's a company (the coordination-and-settlement layer for the agent economy; starts with friends + dinners, generalizes to any group that must agree *and* pay together).

**Sharp-question answers:**
- *"Isn't this just Splitwise?"* → Splitwise splits *after* humans decide, and only tracks IOUs. We do the deciding, strike the booking with the venue's agent, and clear the debt autonomously on an irreversible rail.
- *"What's actually agentic vs scripted?"* → Real: constraint-satisfaction, the venue match, the debt-simplification algorithm, the negotiation protocol. We seed the demo run for stability and keep money-movement deterministic on purpose — you don't want a hallucinating agent moving money.
- *"Where's the other agent from?"* → For the demo it's seeded; in production it's any AP2-compliant merchant agent — the protocol is built for it (merchant signs the cart, buyer co-signs). We're the buyer side nobody's building.
- *"Won't AP2/x402 add this?"* → They're neutral authorization/settlement layers. Multi-party negotiation, group consensus, and debt-optimization are application logic on top. Durable wedge.

---

## 10. Git + the rules

Full workflow is in `GIT_WORKFLOW.md`. The three that matter:
1. **Pull before you start, push when you pause** (never go >1 hour without syncing).
2. **Stay in your folder** (table in §3). Ping the chat before touching `data/*.json`.
3. **Commit small, commit often** — every working chunk is a save point.

---

## 11. The one thing to nail

A working webapp is the price of entry. **Two screens win the room:** the agents arguing their way to the plan (`/waiting`), and your agent striking the deal with the venue's agent (`/confirmed`). Build everything else solid — but rehearse those two beats, and the settlement collapse, until they're flawless. *That's* the difference between "nice app" and "I want to invest."
