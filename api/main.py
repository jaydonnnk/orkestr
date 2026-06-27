"""Orkestr API — FastAPI. Owner: Lucas.

Implements the frontend contract in ORKESTR_FRONTEND.md §4/§6, backed by an
in-memory session store (core/session.py). Seeded session ORK-001 is populated
on startup so every screen has data immediately.

Run from the repo root:
    uvicorn api.main:app --reload --port 8000
"""
import json
import os

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core import session as S

app = FastAPI(title="Orkestr API", version="0.2.0")

_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def _require_session(sid: str) -> dict:
    s = S.get(sid)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return s


def _require_field(body: dict, field: str) -> None:
    if field not in body or body[field] is None:
        raise HTTPException(status_code=400, detail=f"{field} required")


@app.on_event("startup")
def _startup():
    S.seed_demo()


# Also seed at import time so ORK-001 exists however the app is started
# (uvicorn, TestClient, etc.). seed_demo() is idempotent.
S.seed_demo()


# ---- utility ----
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/personas")
def personas():
    return _load("personas.json")


@app.get("/venues")
def venues():
    return _load("venues.json")


# ---- Phase 1: before the meal ----
@app.post("/api/session/start")
def session_start(payload: dict = Body(default={})):
    s = S.new_session(payload.get("name"), payload.get("date_range"))
    return {"session_id": s["session_id"],
            "invite_url": f"https://orkestr.app/join/{s['session_id']}"}


@app.post("/api/constraints")
def constraints(person: dict = Body(...)):
    _require_field(person, "session_id")
    _require_session(person["session_id"])
    _require_field(person, "id")
    S.add_constraints(person["session_id"], person)
    return {"ok": True}


@app.get("/api/status/{sid}")
def status(sid: str):
    s = _require_session(sid)
    if s["phase"] == "negotiating":
        S.compute_plan(sid)  # lazily produce the plan -> plan_ready
    return {"phase": s["phase"]}


@app.get("/api/plan/{sid}")
def plan(sid: str):
    s = _require_session(sid)
    if not s["plan"]:
        S.compute_plan(sid)
    return s["plan"]


@app.get("/api/negotiation/{sid}")
def negotiation(sid: str):
    """NEW — feeds the negotiation RING on /waiting (Act 1 money shot)."""
    s = _require_session(sid)
    if not s["negotiation"]:
        S.compute_plan(sid)
    return s["negotiation"]


@app.post("/api/approve/{sid}")
def approve(sid: str, body: dict = Body(...)):
    s = _require_session(sid)
    _require_field(body, "person_id")
    member_ids = {m["id"] for m in (s["members"] or _load("personas.json"))}
    if body["person_id"] not in member_ids:
        raise HTTPException(status_code=400, detail="unknown person_id")
    S.approve_plan(sid, body["person_id"])
    return {"ok": True}


@app.get("/api/handshake/{sid}")
def handshake(sid: str):
    """Full request -> counter -> mandate, so /confirmed can show the exchange (Act 2)."""
    s = _require_session(sid)
    if not s["handshake"]:
        S.compute_plan(sid)
    return s["handshake"]


# ---- Phase 2: at the meal ----
@app.get("/api/expenses/{sid}")
def expenses(sid: str):
    s = _require_session(sid)
    return s["expenses"]


@app.post("/api/expense/{sid}")
def expense(sid: str, body: dict = Body(...)):
    s = _require_session(sid)
    _require_field(body, "paid_by")
    _require_field(body, "amount")
    if not isinstance(body["amount"], (int, float)) or isinstance(body["amount"], bool):
        raise HTTPException(status_code=400, detail="amount must be numeric")
    if body["amount"] <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    member_ids = {m["id"] for m in (s["members"] or _load("personas.json"))}
    if body["paid_by"] not in member_ids:
        raise HTTPException(status_code=400, detail="paid_by is not a current member")
    S.add_expense(sid, body)
    return {"ok": True}


# ---- Phase 3: after the meal ----
@app.get("/api/settlement/{sid}")
def settlement(sid: str):
    s = _require_session(sid)
    if not s["settlement"]:
        S.recompute_settlement(sid)
    return s["settlement"]


@app.post("/api/settle/{sid}")
def settle_ep(sid: str, body: dict = Body(default={})):
    s = _require_session(sid)
    has_fronted = "fronted" in body
    has_person_id = "person_id" in body
    if not has_fronted and not has_person_id:
        raise HTTPException(status_code=400, detail="person_id or fronted required")
    member_ids = {m["id"] for m in (s["members"] or _load("personas.json"))}
    if has_fronted:
        if not isinstance(body["fronted"], dict):
            raise HTTPException(status_code=400, detail="fronted must be a JSON object")
        bad_keys = [k for k in body["fronted"] if k not in member_ids]
        if bad_keys:
            raise HTTPException(status_code=400, detail="fronted contains unknown member id")
        bad_vals = [v for v in body["fronted"].values()
                    if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0]
        if bad_vals:
            raise HTTPException(status_code=400, detail="fronted values must be numeric >= 0")
    if has_person_id and body["person_id"] not in member_ids:
        raise HTTPException(status_code=400, detail="unknown person_id")
    # All validation passed — apply changes
    if has_fronted:
        S.set_fronted(sid, body["fronted"])        # S11 confirm fronted
    if has_person_id:
        S.approve_transfer(sid, body["person_id"]) # S13 approve transfer
    return {"ok": True}


@app.post("/api/discovery/venues")
def discovery_venues(body: dict = Body(default={})):
    """Exa venue discovery preview — never mutates sessions, never affects ORK-001."""
    from agents import discovery as D

    raw_limit = body.get("limit", 5)
    if raw_limit is not None:
        if not isinstance(raw_limit, (int, float)) or isinstance(raw_limit, bool):
            raise HTTPException(status_code=400, detail="limit must be numeric")
        if raw_limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be > 0")

    query = body.get("query") or None
    constraints = body.get("constraints") or None
    limit = min(int(raw_limit), 10)

    if not query and not constraints:
        query = "Singapore group dinner venue restaurant halal vegetarian options"

    return D.discover_venues(query=query, constraints=constraints, limit=limit)


@app.post("/api/dev/reseed")
def dev_reseed():
    S.SESSIONS.pop("ORK-001", None)
    S.seed_demo()
    return {"ok": True}
