# Orkestr — Feature Deck

> The group chat that never resolves → agents negotiate the plan, book it with the
> venue's agent, and clear the debt. **Splitwise splits after you decide; Orkestr
> does the deciding, strikes the booking, and settles the bill.**

---

## 1. Multi-agent constraint negotiation

Each friend is an agent with real constraints. The Convener proposes venues round
by round; every persona agent reacts based on its *own* constraints — not a script.

```python
# agents/persona.py — each agent objects on its real constraint
if available_days and day not in available_days:
    return {"stance": "object", "constraint_ref": "available_days", ...}
if budget_max is not None and per_person > budget_max:
    return {"stance": "object", "constraint_ref": "budget_max", ...}
```

```python
# agents/convener.py — real rounds: propose → collect 5 stances → converge
for round_no, candidate in enumerate(candidates, start=1):
    evaluations = [stance(p, candidate, round_no) for p in personas]
    if not objections:                       # unanimous → lock it in
        return {"plan": plan, "messages": messages}
    if objection_count <= best_objection_count:   # else keep the least-bad
        best_plan = plan
```

**Why it matters:** the negotiation is genuine constraint-satisfaction. Objections
are evidence-bound (`constraint_ref`), so the ring shows *real* reasons, not theatre.

---

## 2. Real debt-simplification (min cash flow)

Turns a tangle of "who owes whom" into the fewest possible transfers that clear
every balance to zero.

```python
# core/settlement.py — greedy: match biggest debtor to biggest creditor
def simplify(net: dict) -> list:
    cred = sorted(([p, v] for p, v in net.items() if v > 0), key=lambda x: -x[1])
    deb  = sorted(([p, -v] for p, v in net.items() if v < 0), key=lambda x: -x[1])
    while i < len(deb) and j < len(cred):
        amt = min(deb[i][1], cred[j][1])
        transfers.append({"from": deb[i][0], "to": cred[j][0], "amount": amt})
```

**Why it matters:** 5 people, many expenses → collapses to ~3 transfers, nets to
exactly zero. This is the Act-3 "settlement collapse" money shot.

---

## 3. Agentic Commerce Protocol (ACP) — real checkout

The Convener books the venue using OpenAI + Stripe's **Agentic Commerce Protocol**
(spec version `2026-04-17`): create session → counter the time → complete → order.

```python
# payments/acp_checkout.py — merchant-side ACP CheckoutSession lifecycle
create_session(items, buyer, fulfillment)   # status: incomplete
update_session(session_id, ...)              # status: ready_for_payment + counter
complete_session(session_id, payment_data)   # status: completed + order
```

**Why it matters:** not a fake "Booked!" button — the real ACP object lifecycle and
status machine the agent economy is standardizing on.

---

## 4. ACP Delegated Payment via real Stripe

A delegated payment token is minted against a Stripe PaymentIntent, constrained by
an **allowance** (max amount, merchant, expiry) — money moves on a real rail.

```python
# payments/acp_payment.py — real Stripe test-mode PaymentIntent, allowance-bound
payment_intent = stripe.PaymentIntent.create(
    amount=_minor_units(allowance["max_amount"]),
    currency="sgd", payment_method="pm_card_visa",
    payment_method_types=["card"], confirm=True, capture_method="manual",
    metadata={"merchant_id": ..., "checkout_session_id": ..., "expires_at": ...},
)
return {"id": "vt_" + payment_intent.id, "mode": "stripe_test", ...}
```

**Why it matters:** the booking creates and captures a genuine Stripe transaction
(test mode). Money is deterministic on purpose — you don't want a hallucinating
agent moving funds.

---

## 5. Agent-to-agent handshake (the counter-offer)

Your buyer agent asks for 7:00; the venue's agent counters 7:30; both co-sign. The
full `request → response → mandate` is exposed for the `/confirmed` screen.

```python
# ai/narrate.py — the two agents talking
"Your agent asks: table for 5 on FRI at 19:00."
"Seoul Garden's agent counters: 19:00 is full, 19:30 is open."
"Both agents co-sign - booking SG-2026-0627-77 is locked in."
```

**Why it matters:** *"the future isn't you transacting with a person — it's your
agent transacting with theirs."* This is the headline demo beat.

---

## 6. Live web venue discovery (Exa)

For real (non-demo) groups, Orkestr searches the **live web** via the Exa API for
venues that fit the group — not a fixed list.

```python
# agents/discovery.py — query is built from the group's real constraints
"Singapore group dinner venue for 5 people halal-friendly no raw fish
 serving meat dishes and vegetarian options budget 40 to 120 SGD per person"
# → Exa returns real restaurants, scraped for halal / vegetarian / price signals
```

**Why it matters:** the system generalizes beyond seeded data — point it at any
group and it finds genuine, bookable venues in real time.

---

## 7. Constraint-fit ranking (smart discovery)

Discovered venues are ranked by how many of the group's constraints they actually
satisfy, so a real fit beats an arbitrary keyword match.

```python
# agents/discovery.py — score mirrors the negotiation's own stance logic
def _venue_fit_score(venue, personas):
    if price > budget_max:                 score -= 1   # over someone's cap
    if "halal" in diet and not halal:      score -= 1
    if wants_meat and is_veg_only:         score -= 1   # all-veg fails meat eaters
    return score
# an all-vegetarian venue drops to 0 for a mixed group; omnivore venues win
```

**Why it matters:** stops a "Halal Vegan Menu" from winning a group that includes a
steak lover. Discovery quality, not just discovery.

---

## 8. Session state machine + seeded demo

A clean phase machine drives all 14 screens; a pre-seeded group (`ORK-001`) gives
every screen real data on boot — no 5-way live sync to debug on stage.

```python
# core/session.py
PHASES = ["negotiating", "plan_ready", "booking", "confirmed"]
# ORK-001 is contractually FROZEN to demo-perfect values; live sessions run the
# real engine + Exa.  if sid != "ORK-001":  ... add Exa venues ...
```

**Why it matters:** "real endpoints, seeded data underneath" — the demo is stable
*and* every call is a real API call.

---

## 9. x402 settlement rail

Each simplified transfer is settled on a stablecoin-style rail, stamped with a tx
hash and latency.

```python
# payments/x402.py
def settle(transfers):
    return [{**t, "rail": "x402", "status": "settled",
             "tx_hash": stamp(), "latency_ms": random.randint(800, 1500)}
            for t in transfers]
```

**Why it matters:** the debt clears autonomously on an irreversible rail — Splitwise
only tracks IOUs; Orkestr actually moves the money.

---

## 10. Graceful degradation everywhere

Every external dependency (Stripe, Exa, OpenAI) has a safe fallback. A missing key
or a network failure never crashes the demo.

```python
# payments/acp_payment.py
if not secret_key.startswith("sk_test_"):
    return _mock_token(allowance)          # no key → mock, demo still runs
except Exception as exc:
    return _mock_token(allowance)          # Stripe error → mock, never 500
```

**Why it matters:** on-stage resilience. Wifi dies, a key expires — the flow still
completes end to end.

---

## 11. Append-only audit log

Every plan, handshake, mandate, and transfer is recorded — an immutable trail of
what the agents did.

```python
# core/audit.py
def record(event, payload):
    f.write(json.dumps({"ts": time.time(), "event": event, "payload": payload}) + "\n")
```

**Why it matters:** agent actions are accountable and replayable — important the
moment agents move real money.

---

## 12. Clean REST contract (frontend ↔ backend)

A stable, documented API: 14 screens talk to one set of endpoints; flip one env var
(`USE_MOCK`) to swap mock data for the live backend with zero screen changes.

```
POST /api/session/start      GET  /api/negotiation/{id}   # feeds the ring
POST /api/constraints        GET  /api/handshake/{id}      # feeds the handshake
GET  /api/status/{id}        GET  /api/settlement/{id}     # feeds the collapse
POST /api/approve/{id}       POST /api/settle/{id}
```

**Why it matters:** clean separation let four people build in parallel and integrate
in hours, not days.

---

## One-line architecture

```
Next.js (Vercel) ──HTTP──> FastAPI (Railway)
                              ├─ agents/    negotiation + booking
                              ├─ core/      session, settlement, audit
                              ├─ payments/  ACP checkout + Stripe + x402
                              └─ ai/        Exa discovery + LLM narration
```
