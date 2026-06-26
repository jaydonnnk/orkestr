# Orkestr — Build Guide & Hackathon Timeline
### Build2026 · Saturday 27 June · 9:00 AM – 9:00 PM

> **Orkestr is the plan that never gets made — made in two minutes, booked with the venue's own agent, and paid for before anyone leaves the chat.**
>
> Every group has the same dead thread: *"where should we eat Friday?" → "idk anywhere" → "you decide" → [three days of silence]*. Orkestr gives each person an agent that holds their real constraints, lets the agents negotiate to a plan everyone would actually agree to, **strikes the booking with the venue's own agent**, and then settles every share automatically on x402 — so nobody ever sends *"can you pay me back"* again.

**Theme:** Trust, Commerce & Fraud × The Future of Work (agent-to-agent coordination + settlement as the primitive).
**One-line pitch:** *Splitwise tracks the bill after you've decided. Orkestr's agents do the deciding, strike the deal, and clear the debt themselves.*

---

## 0. Read this first — the demo IS the product

Everyone builds toward **one ~2-minute sequence in three acts**. Two crowd-pleasing money shots bookend one genuinely novel beat in the middle. Protect all three.

**Cold open — the pain.** A real group chat, half-dead: *"where do we eat??" · "anywhere lah" · "you decide" · [seen, no reply]*. One line: *"Five people, three days, zero decisions. Everybody's been here."*

**🎯 Act 1 — CONVERGE (money shot 1).** Five friends, five **agents**, each loaded with real constraints (free days, budget cap, dietary, travel limit). Hit **Orkestrate**. The five avatars negotiate in a ring — constraints clash on screen (*Bob caps at $40 · Carol can't do Saturday · Dave won't eat raw fish*), candidate plans narrow **3 → 2 → 1**, and a plan **crystallizes**: venue, time, activity. It feels like watching a group chat resolve itself in ten seconds.

**⭐ Act 2 — TRANSACT (the novel peak).** The plan is set, but nothing is booked. The **Convener agent** opens a channel to **Seoul Garden's own booking agent** — and *the two agents transact*. Convener: *"table for 5, Friday 7pm, halal, veg option, ~$400."* The venue agent checks, counters: *"7pm full — 7:30 open, $48 a head, halal ✓, veg ✓."* They agree, and **co-sign an AP2 mandate**: the venue signs the cart first (its guarantee of price + terms — *what you see is what you pay for*), the Convener authorizes payment for the group. **Booking confirmed ✓ · Mandate co-signed ✓.** This is the beat everyone remembers — *the future isn't you transacting with a person; it's your agent transacting with theirs.*

**The canvas.** The locked plan renders — map with venue + arcade pinned, a clean itinerary card, the booking reference. (TripCanvas energy: messy input → gorgeous artifact.)

**🎯 Act 3 — SETTLE (money shot 2).** A **who-owes-whom graph** appears, and it's a *tangle* — Alice fronted the $240 table, Bob bought $100 of arcade credit, Carol covered $60 of drinks. Each friend taps **Approve**; their pre-authorized share releases (Intent Mandate ✓). **x402** micropayments fire along the edges in real time; the tangle **simplifies to three clean transfers** and then **collapses to all-zeros**. A green **"Settled"** passport renders.

**The closing line:** *"The plan that never gets made — made in two minutes. Your agent argued it out with four others, struck the booking with the restaurant's own agent, and squared everyone up on a rail where the money is final. Nobody decided. Nobody chased. It just happened."*

**The three non-negotiables:** the *converge* beat, the *agent-to-agent co-sign* beat, and the *settlement collapse* beat. The bookends win the smile; the middle wins the *"oh — that's the future."*

---

## 1. What we're building (plain version)

Each person hands their agent a small bundle of constraints (and one freeform line). The **Convener agent** turns those into candidate plans, the agents run a short **negotiation protocol** to converge on one, the Convener **strikes the booking with the Venue agent** and the two co-sign an AP2 mandate, and the **Settlement agent** assigns who-fronts-what, computes the *minimal* set of transfers, and clears them on x402.

```
Intake (5 personas + constraints)
  → Convener generates candidate plans (LLM over freeform prefs)
  → ACT 1  CONVERGE: negotiation rounds (propose → object → concede → accept) → one plan
  → ACT 2  TRANSACT: Convener ↔ Venue agent → booking + co-signed AP2 cart mandate
  → render plan on canvas (map + itinerary + booking ref)
  → friends approve → shares release against their Intent Mandates
  → ACT 3  SETTLE: net balances → DEBT SIMPLIFICATION → minimal x402 transfers → collapse to zero
  → "Settled" passport + audit log
```

**Be honest with yourselves about what's real vs. staged** — this is what keeps it feasible *and* lets you answer sharp judges without flinching:

- **Genuinely agentic / real algorithm:** the LLM reasoning that turns five messy freeform preferences into structured candidate plans; the **constraint-satisfaction** scoring that ranks plans; the **Venue agent** matching the group's needs against its attributes and quoting terms; and the **debt-simplification** that collapses the settlement graph (a real min-cash-flow algorithm — §8).
- **Real protocol, seeded outcome:** the negotiation and the venue handshake run on real data, but the *rounds and the quote are seeded* so the demo fires identically every time. The co-signed mandate is AP2-accurate (merchant signs the cart, buyer authorizes).
- **Pure theater (and that's fine):** the avatar choreography and the per-edge settlement animation. They sell the story; they don't decide anything.

> **Determinism in the money-movement is a feature, not a shortcut.** You do not want a hallucinating LLM deciding who pays whom, or letting a tampered cart through. The agents *negotiate, authorize, and co-sign*; deterministic logic *moves the money*. Say that out loud — it makes you look sharper than teams pretending there are seven reasoning LLMs live.

---

## 2. The JSON contract — lock this in Hour 1 (parallelization key)

This is how four people work without blocking each other. **Backend, Frontend, and AI all build against these shapes from ~9:45 onward.** Paste it in the repo README; don't change it after Phase 1 without telling everyone.

**Person + constraints** (intake → everything):
```json
{
  "id": "P-002",
  "name": "Bob",
  "avatar": "bob.png",
  "constraints": {
    "available_days": ["FRI", "SUN"],
    "budget_max": 40,
    "dietary": ["no_raw_fish"],
    "max_travel_min": 30,
    "origin": "Tampines"
  },
  "freeform": "broke this week, somewhere chill, not raw fish"
}
```

**Candidate plan / Cart** (Convener produces, UI + AP2 + Venue agent consume):
```json
{
  "plan_id": "PLAN-1",
  "title": "Korean BBQ + arcade",
  "day": "FRI",
  "time": "19:30",
  "venue": { "name": "Seoul Garden", "lat": 1.3010, "lng": 103.8480, "place_id": "..." },
  "activity": { "name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222 },
  "total_cost": 400,
  "per_person": 80,
  "satisfies": ["P-001","P-002","P-003","P-004","P-005"],
  "conflicts": []
}
```

**Negotiation message** (drives Act 1 / Money Shot 1):
```json
{
  "round": 2,
  "agent": "P-002",
  "stance": "object",            // propose | object | concede | accept
  "claim": "Saturday is out — Bob isn't free",
  "targets_plan": "PLAN-2",
  "constraint_ref": "available_days"
}
```

**Venue handshake** (drives Act 2 — the agent-to-agent beat):
```json
{
  "from": "convener",
  "to": "venue:seoul_garden",
  "request": { "party_size": 5, "day": "FRI", "time": "19:00",
               "budget_total": 400, "needs": ["halal","vegetarian_option"] },
  "response": {
    "available": true,
    "time_offered": "19:30",          // venue counters the time
    "price_total": 240,
    "per_head": 48,
    "meets": ["halal","vegetarian_option"],
    "hold_id": "HOLD-77"
  }
}
```

**Co-signed mandate** (output of the handshake — AP2-shaped):
```json
{
  "cart_id": "CART-1",
  "merchant": "Seoul Garden",
  "items": [{ "desc": "KBBQ set · table of 5 · FRI 19:30", "amount": 240 }],
  "merchant_signature": "0xVENUE…",     // venue agent signs the cart FIRST (the guarantee)
  "buyer_authorization": "0xCONVENER…", // convener authorizes payment for the group
  "status": "co-signed",                // co-signed | tampered | declined
  "booking_ref": "SG-2026-0627-77"
}
```

**Settlement plan + transfers** (drives Act 3 / Money Shot 2):
```json
{
  "fronted":  { "P-001": 240, "P-002": 100, "P-003": 60, "P-004": 0, "P-005": 0 },
  "shares":   { "P-001": 80,  "P-002": 80,  "P-003": 80, "P-004": 80, "P-005": 80 },
  "net":      { "P-001": 160, "P-002": 20,  "P-003": -20, "P-004": -80, "P-005": -80 },
  "transfers": [
    { "from": "P-004", "to": "P-001", "amount": 80, "rail": "x402", "status": "settled", "tx_hash": "0x…", "latency_ms": 1100 },
    { "from": "P-005", "to": "P-001", "amount": 80, "rail": "x402", "status": "settled", "tx_hash": "0x…", "latency_ms": 1300 },
    { "from": "P-003", "to": "P-002", "amount": 20, "rail": "x402", "status": "settled", "tx_hash": "0x…", "latency_ms":  900 }
  ],
  "net_after": { "P-001": 0, "P-002": 0, "P-003": 0, "P-004": 0, "P-005": 0 }
}
```

---

## 3. Team & ownership

| Role | Owner | Owns |
|---|---|---|
| **Backend / Agents (lead)** | **Jaydon** | Convener + negotiation orchestration (propose/object/concede/accept); the **Convener side of the venue handshake** (booking request, payment authorization, the **AP2 mandate format + co-sign**); the **Settlement agent** (net balances → **debt simplification** → x402 transfer set). **Doubles as pitch lead from 6:00 PM.** |
| **Backend / Data + API + Venue Agent** | **Lucas** | Persona + venue datasets, candidate-venue seed data, **FastAPI endpoints**, the **x402 settlement mock** (transfer sequencing + latency), SQLite + append-only audit log — **and the Venue Agent: the other side of the handshake** (checks availability, matches the group's needs, quotes/counters terms, signs the cart, confirms the booking). |
| **Frontend / Design** | **Leeshan** | All screens. The **negotiation ring** (Act 1), **the handshake beat** (venue node appears, two-agent request→counter→agree, the co-sign lock), the **canvas** (map + itinerary), the **settlement graph** (tangle → collapse, Act 3), the approval flow, the "Settled" passport. |
| **AI / Narration + Demo Ops** | **Nigel** | The LLM that turns freeform prefs → **candidate plans**; **evidence-bound** per-agent negotiation lines (narrate only the real constraint — never invent a reason); the **venue-agent dialogue copy**; the "Settled" copy. **Plus demo insurance:** seeds the scenario, records the backup video, runs click-through QA, builds the cold-open mockup. (High-value work that blocks nobody.) |

**The handshake split is deliberate.** Jaydon owns the **Convener side**, Lucas owns the **Venue side** — they build to the **co-signed-mandate contract** between them, which *is* the agent-to-agent transaction. Two people, two agents, one signed artifact, mirroring the real thing.

**The two-backend boundary (agree at kickoff):**
- **Lucas** owns *data → API → Venue agent → x402 settlement mock → audit*.
- **Jaydon** owns *Convener → negotiation → AP2 mandate/co-sign → debt-simplification*.
- You meet at the **plan object**, the **co-signed mandate**, and the **settlement plan**.

---

## 4. Hour-by-hour timeline

> Effective build is ~10 hrs after lunch, a workshop, and demo prep. Shape: **core done by ~3:00, integration by 4:30, then polish + rehearsal + buffer.** For a demo-scouted Proof-of-Work hackathon, an over-rehearsed flawless run is the edge — do not skimp the back half.

### Phase 0 — Alignment & contracts · 9:00–9:45 (whole team)
The highest-leverage 45 minutes of the day.
- Lock the **demo script** (§0) — everyone builds toward the three acts.
- Lock the **5 personas + the venue seed + the one scenario** (§5).
- Lock the **JSON contract** (§2) in the README — including the **venue handshake + co-signed mandate** shapes.
- Repo, folder structure, shared env (OpenAI key — use the Codex/OpenAI credits), branch strategy.
- **Decision:** Next.js + FastAPI. The whole product is the visual; play to the design strength. Streamlit only if FE is genuinely at risk.

### Phase 1 — Foundations in parallel · 9:45–11:30
| Owner | Task |
|---|---|
| **Lucas** | Build 5 personas + constraints + 3 candidate venues with attributes (halal/veg/price/capacity/hours). Stand up SQLite + loaders + FastAPI skeleton. **Stub the Venue agent** returning a canned availability/price response in the handshake shape. |
| **Jaydon** | Scaffold the agent framework + **AP2 mandate mock**. Stub the negotiation loop (valid `negotiation_message` shapes) **and the Convener→Venue request + co-sign stub**. |
| **Leeshan** | UI shell against mock JSON: the **negotiation ring**, **the handshake area** (a venue node + a two-agent exchange strip + co-sign lock), the **canvas**, the **settlement graph** component, routing. *(If Cleon's design workshop runs this morning, attend, then come back with direction.)* |
| **Nigel** | Write the **freeform-prefs → candidate-plans** prompt, the **evidence-bound negotiation** prompt, and the **venue-agent dialogue** prompt. Test on hand-written data. Build the cold-open group-chat mockup. |

**Milestone @ 11:30:** personas + venues load, negotiation + handshake stubs return valid shapes, UI renders all four surfaces on mock data, narration works on fakes.

### Phase 2 — Core engine working · 11:30–1:00 *(stagger lunch in here)*
| Owner | Task |
|---|---|
| **Lucas** | **Venue agent for real**: match the group's `needs` against venue attributes, offer a time (counter if the ask is full), quote price → real handshake response. x402 settlement mock sequences transfers with latency. Endpoints finalized. |
| **Jaydon** | **Constraint-satisfaction** (score every venue×day×time vs all 5 constraints → best plan) + **negotiation rounds** on real constraints. Wire **Convener → Venue request → receive response → co-sign the cart mandate**. |
| **Leeshan** | Ring renders real negotiation messages; the **handshake renders the real two-agent exchange** (request → counter → agree → co-sign lock); canvas renders the crystallized plan + booking ref; settlement graph renders real edges. |
| **Nigel** | Candidate-plan generation on the **real** freeform fields; negotiation lines bound to real `constraint_ref`s; **venue dialogue runs on the real handshake data**. |

**Milestone @ 1:00:** one scenario flows end-to-end — constraints in → plan out → **booking co-signed** → settlement graph drawn (even if ugly).

### Phase 3 — The three beats land · 1:00–3:00
This is the differentiator. Protect this block.
| Owner | Task |
|---|---|
| **Jaydon** | **Debt simplification** (net balances → minimal transfer set — §8). The **AP2 share-release** path (each member's Intent Mandate authorizes their slice). Finalize the **co-signed cart** path; wire settlement → x402. |
| **Lucas** | Audit log writes every plan + handshake + mandate + transfer. **Booking confirmation** (`booking_ref`) returned and shown. The "Settled" net-zero proof assembled. |
| **Leeshan** | **Act 1:** ring *alive* — proposing/objecting, candidates 3→1, plan crystallizing. **Act 2:** the **handshake as a featured beat** — venue node slides in, request→counter→agree, **co-sign lock snaps shut** with "Booking confirmed ✓". **Act 3:** the **tangle → 3 transfers → collapse-to-zero** + "Settled" passport. |
| **Nigel** | Narration per negotiation round; **venue-agent dialogue lines**; "Settled" copy ("Everyone's square. Nobody's chasing anybody."). |

**Milestone @ 3:00:** full seed scenario produces the correct plan → co-signed booking → settlement through the whole stack, all three beats firing. Core build done.

### Phase 4 — Integration · 3:00–4:30
Where hackathons die — budget the real time. Whole team wires FE ↔ API ↔ agents ↔ AI. Run the seed scenario (and the backup scenario) through the live stack repeatedly. Fix every break. **No new features.**

**Milestone @ 4:30:** end-to-end works live, no console errors, all three beats clean.

### Phase 5 — Demo flow + polish · 4:30–6:00
Make all three beats *buttery*.
- Perfect the sequence: cold-open → Orkestrate → ring converges → **venue handshake + co-sign** → canvas → approve → tangle collapses → Settled.
- Seed the **exact** scenario so it fires identically every run.
- Tune timings: ring ~12s; handshake ~8s (request→counter→agree→lock); settlement collapse ~3s. Motion only where it earns attention.

### Phase 6 — Rehearse + backup · 6:00–7:30
- **Jaydon shifts to pitch lead** (backend stable). Lock the **4-minute pitch**.
- Run pitch + demo **end to end, repeatedly**, on the actual presenting machine.
- **Nigel records the backup video** of the full run — demo insurance if the wifi dies.
- Drill **Q&A** (§7).

### Phase 7 — Final polish + buffer · 7:30–8:30
Hold as buffer. **If ahead**, add *one* flourish — the strongest is the **tampered-cart catch**: the venue agent's signed cart is altered after signing (price bumped), the co-sign check **breaks**, and Orkestr blocks the booking. It proves the co-signature *does something* and reinforces the trust theme in ten seconds. (Alternative: a second scenario with bigger numbers.) Nice-to-have only; never at the demo's expense.

### Tools down · 8:30–9:00
Stop building. Final rehearsal. Present.

---

## 5. Demo personas + venue seed + scenario

**Five friends, one Friday night.** Tune constraints so the negotiation has *visible* tension that resolves cleanly.

| Persona | Free days | Budget | Dietary | Travel | Freeform |
|---|---|---|---|---|---|
| **Alice** | FRI, SAT | $120 | — | 45m | "down for anything fun, happy to book" |
| **Bob** | FRI, SUN | $40 | no raw fish | 30m | "broke this week, somewhere chill" |
| **Carol** | FRI | $90 | vegetarian | 40m | "needs veg options, loves a good arcade" |
| **Dave** | FRI, SAT | $100 | — | 60m | "anywhere with good meat" |
| **Eve** | FRI, SAT | $80 | halal | 30m | "halal please, walkable area" |

**Venue seed (what the Venue agent reasons over):**

| Venue | Halal | Veg | $/head | Capacity | Hours | Near arcade |
|---|---|---|---|---|---|---|
| **Seoul Garden** | ✓ | ✓ | $48 | 6 | 17:00–23:00 | ✓ (Timezone) |
| Sushi Hiro | ✓ | — | $70 | 8 | 18:00–22:00 | — |
| Veggie Table | ✓ | ✓ | $35 | 4 | 12:00–21:00 | — |

**Why it resolves to Seoul Garden + arcade (FRI, 19:30):** only **FRI** clears all five (Carol's hard constraint). The venue must satisfy **Bob's $40 share-ceiling**, **Carol's veg**, **Eve's halal + walkable**, **Dave's meat**, and sit **near an arcade** → Seoul Garden is the only seed that hits everything. In the handshake, **7pm is full so the venue agent counters 7:30** — a small, real negotiation the audience sees.

**The settlement tangle (why Act 3 lands):** different people front different things, so the naive graph is a mess that simplification collapses.

- Total **$400**, per-person **$80**. (Dinner $240 via the co-signed booking + arcade $100 + drinks $60.)
- Fronted: **Alice $240** (the table, co-signed with the venue), **Bob $100** (arcade), **Carol $60** (drinks), Dave $0, Eve $0.
- Net: Alice **+160**, Bob **+20**, Carol **−20**, Dave **−80**, Eve **−80**.
- **Minimal transfers (3):** Dave→Alice $80, Eve→Alice $80, Carol→Bob $20. Everyone ends at **0**.

> Run order in the pitch: cold-open → **converge** (hook) → **handshake/co-sign** (the novelty) → canvas → **settlement collapse** (the kill). Keep a **second scenario** (weekend trip, bigger numbers) seeded as backup.

---

## 6. Scope discipline — cut without guilt

**Do NOT build:** live AP2/x402 SDK integration (mock the mandate as signed JSON; mock x402 as a sequenced transfer list), **live venue/booking APIs** (the Venue agent is a *seeded module* reasoning over `venues.json`, not an OpenTable integration), real wallets/on-chain anything, real auth/accounts (preset personas), Instagram/Reel parsing, more than ~5 personas, more than 2 scenarios, real-time human multiplayer.

**The slice is:** *constraints in → agents negotiate to one plan → Convener and Venue agent co-sign the booking → render on canvas → each share authorized → debts simplified and cleared on x402 → collapse to zero.* Everything else is something you **say in the pitch**, not something you build.

**Backup plan:** if the live negotiation or handshake gets flaky, **hard-code the seeded scenario's rounds, the venue's counter, and the outcome**. Judges remember the product logic and the demo, not live robustness on inputs you'll never show. Never let one module sink the run.

---

## 7. Pitch & Q&A

**The 4-minute arc:** the pain (group coordination is a tax everyone pays and nobody solves — polls don't decide, and someone always eats the cost) → the shift (*the future isn't you transacting with a person; it's your agent transacting with theirs*) → **the demo** (converge → **agent-to-agent co-sign** → settlement collapse) → why it's a company (the coordination-and-settlement layer for the agent economy; starts with friends + dinners, generalizes to teams, housemates, any group that has to agree *and* pay together).

**Armed answers for the sharp questions:**
- *"Isn't this just Splitwise?"* → Splitwise splits the bill **after** humans decided everything, and it only tracks IOUs — you still chase people. Orkestr's agents do **the deciding** (the hard part), **strike the booking** with the venue's own agent, and **clear** the debt autonomously on an irreversible rail. The split is our last step, not our product.
- *"Where does the 'other' agent come from / is the venue agent real?"* → For the demo it's a seeded counterpart. In production it's **any AP2-compliant merchant agent** — the protocol is built for exactly this: the merchant signs the cart (its price/terms guarantee), the buyer co-signs. We're showing the *group-buyer* side of an agent-to-agent transaction, which is the half nobody else is building.
- *"What's actually agentic vs. scripted?"* → The LLM genuinely reasons over messy freeform preferences to generate candidate plans; constraint-satisfaction, the venue match, and **debt simplification** are real algorithms; the negotiation and handshake protocols are real. We seed the demo run for stability and keep money-movement deterministic **on purpose** — you don't want a hallucinating agent deciding who pays whom or waving through a tampered cart.
- *"Won't AP2/x402 just add this?"* → They're deliberately **neutral** authorization and settlement layers. Multi-party negotiation, group consensus, the buyer-side handshake, and debt-optimization are application logic — out of scope for, and against the neutrality of, a global payment protocol. We sit on top and bring the group's intent to bear. Durable wedge.
- *"Is the money real?"* → We mock the rails for the demo (correctly — integrating a live SDK in a day is a trap). The mandate shapes are AP2-accurate, the co-sign is the real merchant-signs-then-buyer-signs pattern, and the settlement is x402-modeled. Productionizing is wiring, not invention.

---

## 8. Tech stack + the one real algorithm

| Layer | Choice | Note |
|---|---|---|
| Frontend | **Next.js + React** (fallback: Streamlit) | The product *is* the visual. |
| Ring · handshake · settlement graph | **Hand-rolled SVG + CSS transitions** | For a fixed, seeded layout this beats a graph library — total control over timing, no surprises mid-demo. |
| Canvas / map | Lightweight map component, seeded pins | TripCanvas-style; keep it controllable. |
| Backend | **FastAPI** | Async, fast to stand up. |
| DB | **SQLite** | Portable, inspectable, audit log. |
| Agents | Convener · persona · **venue** · settlement modules | Mostly deterministic; 1–2 LLM-narrated. |
| LLM | **OpenAI / Codex** (credits provided), explanation + plan-gen + dialogue, evidence-bound | Never invents a constraint, a quote, or a verdict. |
| Mandate | **Mocked signed JSON** (AP2-shaped), merchant-then-buyer co-sign | Do not integrate the live SDK. |
| Settlement | **x402-modeled** transfer sequence | Mock; latency for theater. |

**The debt-simplification (your "technical enough" centerpiece — make it real):**
```python
def simplify(net: dict[str, int]) -> list[dict]:
    # net = paid - owed, per person; sums to 0
    cred = sorted(([p, v]  for p, v in net.items() if v > 0), key=lambda x: -x[1])
    deb  = sorted(([p, -v] for p, v in net.items() if v < 0), key=lambda x: -x[1])
    transfers, i, j = [], 0, 0
    while i < len(deb) and j < len(cred):
        amt = min(deb[i][1], cred[j][1])
        transfers.append({"from": deb[i][0], "to": cred[j][0], "amount": amt})
        deb[i][1] -= amt; cred[j][1] -= amt
        if deb[i][1] == 0: i += 1
        if cred[j][1] == 0: j += 1
    return transfers   # greedy min-cash-flow: biggest debtor → biggest creditor
```
Deterministic, instant, and it's the thing that makes the tangle collapse to *three* clean edges instead of a hairball. Feature it when a technical judge asks what's under the hood.

**Repo skeleton:**
```
orkestr/
  data/
    personas.json          # the 5 friends + constraints
    venues.json            # seeded venues + attributes (the Venue agent's world)
  core/
    constraints.py         # score plans vs all constraints
    settlement.py          # net balances + simplify() (the algorithm)
    audit.py               # append-only log
  agents/
    convener.py            # candidate plans + negotiation + venue handshake (buyer side)
    persona.py             # per-person stance: propose|object|concede|accept
    venue.py               # THE OTHER SIDE: availability, quote/counter, sign cart, confirm
    settlement_agent.py    # who-fronts-what → simplify → x402 transfer set
  payments/
    mandate.py             # AP2-shaped: merchant-signs-then-buyer co-sign; share-release
    x402.py                # settlement mock: sequence transfers + latency
  ai/
    plan_gen.py            # freeform prefs → candidate plans (LLM)
    narrate.py             # evidence-bound negotiation + venue dialogue + "Settled" copy
  api/
    main.py                # FastAPI endpoints
  frontend/                # Next.js (ring, handshake, canvas, settlement graph, passport)
  mandates/
    sample_mandate.json
  README.md                # the JSON contract lives here
```

---

## Pre-game (you have until Saturday)

Two days out, the cheap wins to bank *before* the clock starts:
- **Personas + venue seed + scenario finalized** (copy §5 into `personas.json` / `venues.json`). Numbers tuned so the negotiation visibly resolves, **the venue counters 7→7:30**, and the settlement tangles-then-collapses.
- **Repo skeleton committed**, README with the full JSON contract (incl. handshake + co-signed mandate), OpenAI key in env, Next.js + FastAPI hello-world both running.
- **Design refs** for the ring, the handshake beat, and the settlement graph so Leeshan starts with direction, not a blank canvas.
- **The cold-open screenshot** (a believably dead group chat) mocked up — first thing judges see, costs nothing now (Nigel).

---

## 9. The one thing to nail

Three acts, one product: **converge → transact → settle.** If judges remember anything, it must be: *five agents argued their way to the plan the group could never agree on, your agent struck the booking with the restaurant's own agent and co-signed it, and then the money squared itself and vanished off the table.* The two money shots win the smile; the **agent-to-agent co-sign in the middle is the one that makes a VC lean forward.** Rehearse the whole arc until it's muscle memory — and protect the co-sign beat, because it's the most novel thing in the room.
