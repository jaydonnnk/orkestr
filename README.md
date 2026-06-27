# Orkestr

**The plan that never gets made — made in two minutes, booked with the venue's own agent, and paid for before anyone leaves the chat.**

Group coordination + autonomous settlement. Agents negotiate a plan everyone accepts,
the Convener strikes the booking with the venue's own agent (co-signed AP2 mandate),
then the bill settles itself on x402 — minimal transfers, nobody chasing anybody.

Built for 'Sup **Build2026** (27 Jun 2026). **Full 14-screen webapp.**

- Frontend guide (source of truth for the UI): [`docs/ORKESTR_FRONTEND.md`](docs/ORKESTR_FRONTEND.md)
- Build guide (being revised to v2 for the full-product scope): [`docs/Orkestr_Build_Guide.md`](docs/Orkestr_Build_Guide.md)

---

## Architecture

```
frontend/  →  Next.js app (14 screens, cream/coral) — build from ORKESTR_FRONTEND.md
   │  HTTP (lib/api.js)
   ▼
backend (repo root)  →  FastAPI implementing the frontend's REST contract
   │
   ▼
core/session.py  →  in-memory session store + state machine, seeded session ORK-001
```

**Hackathon approach:** real endpoints, **seeded data underneath**. Every screen and route
is real; the negotiation, plan, handshake, and settlement come from seeded session state, so
nobody debugs multi-user sync at 8pm. Swap the stubs for real logic without touching the API.

---

## Run

### Backend — from the repo root
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
Seeded session **ORK-001** is populated on boot, so every screen has data immediately.

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```
Set `NEXT_PUBLIC_API_URL=http://localhost:8000`, `NEXT_PUBLIC_USE_MOCK=false` once backend is up.

---

## API (matches ORKESTR_FRONTEND.md §4/§6)

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/session/start` | Create event → `{session_id, invite_url}` |
| POST | `/api/constraints` | Submit a member's constraints |
| GET | `/api/status/{id}` | `negotiating` → `plan_ready` → `booking` → `confirmed` |
| GET | `/api/negotiation/{id}` | **the 3→1 messages — feed the negotiation RING (Act 1)** |
| GET | `/api/plan/{id}` | The crystallized plan |
| POST | `/api/approve/{id}` | Approve plan / release deposit |
| GET | `/api/handshake/{id}` | **request → counter → mandate — the agent handshake (Act 2)** |
| GET | `/api/expenses/{id}` · POST `/api/expense/{id}` | Logged expenses |
| GET | `/api/settlement/{id}` | fronted · shares · net · transfers · net_after |
| POST | `/api/settle/{id}` | Confirm fronted / approve a transfer (Act 3) |

> Two endpoints (`/api/negotiation`, full `/api/handshake`) were **added** so the two money
> shots — agents negotiating, and your agent transacting with the venue's — have a home in
> the 14-screen flow. Render the ring on `/waiting` and the exchange on `/confirmed`.

## What already works vs. stub

- **Works now:** the full session state machine, all endpoints, the real debt-simplification
  (`core/settlement.py`) driven by logged expenses, the x402 + AP2 co-sign mocks, and seeded
  ORK-001 (plan_ready, 10 negotiation messages, co-signed handshake, 3 expenses, 3 transfers
  netting to zero).
- **Stubs (see build guide phases):** real constraint-satisfaction, real negotiation rounds,
  LLM plan-gen/narration, the Venue agent's real attribute matching.

## Team

| Owner | Area |
|---|---|
| **Jaydon** | Convener + negotiation + AP2 co-sign + settlement · pitch lead |
| **Lucas** | Session store + the REST API (this backend) + x402 mock |
| **Leeshan** | The 14-screen frontend (cream/coral) — `ORKESTR_FRONTEND.md` |
| **Nigel** | AI/narration (plan-gen, dialogue, copy) + demo ops (seed, backup video, QA) |
