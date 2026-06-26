"""Orkestr API — FastAPI. Owner: Lucas.

Implements the frontend contract in ORKESTR_FRONTEND.md §4/§6, backed by an
in-memory session store (core/session.py). Seeded session ORK-001 is populated
on startup so every screen has data immediately.

Run from the repo root:
    uvicorn api.main:app --reload --port 8000
"""
import json
import os

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import session as S

app = FastAPI(title="Orkestr API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


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
    S.add_constraints(person["session_id"], person)
    return {"ok": True}


@app.get("/api/status/{sid}")
def status(sid: str):
    s = S.get(sid)
    if not s:
        return {"phase": "negotiating"}
    if s["phase"] == "negotiating":
        S.compute_plan(sid)  # lazily produce the plan -> plan_ready
    return {"phase": s["phase"]}


@app.get("/api/plan/{sid}")
def plan(sid: str):
    s = S.get(sid)
    if s and not s["plan"]:
        S.compute_plan(sid)
    return s["plan"] if s else None


@app.get("/api/negotiation/{sid}")
def negotiation(sid: str):
    """NEW — feeds the negotiation RING on /waiting (Act 1 money shot)."""
    s = S.get(sid)
    if not s:
        return []
    if not s["negotiation"]:
        S.compute_plan(sid)
    return s["negotiation"]


@app.post("/api/approve/{sid}")
def approve(sid: str, body: dict = Body(...)):
    S.approve_plan(sid, body["person_id"])
    return {"ok": True}


@app.get("/api/handshake/{sid}")
def handshake(sid: str):
    """Full request -> counter -> mandate, so /confirmed can show the exchange (Act 2)."""
    s = S.get(sid)
    return s["handshake"] if s else None


# ---- Phase 2: at the meal ----
@app.get("/api/expenses/{sid}")
def expenses(sid: str):
    s = S.get(sid)
    return s["expenses"] if s else []


@app.post("/api/expense/{sid}")
def expense(sid: str, body: dict = Body(...)):
    S.add_expense(sid, body)
    return {"ok": True}


# ---- Phase 3: after the meal ----
@app.get("/api/settlement/{sid}")
def settlement(sid: str):
    s = S.get(sid)
    if not s:
        return None
    if not s["settlement"]:
        S.recompute_settlement(sid)
    return s["settlement"]


@app.post("/api/settle/{sid}")
def settle_ep(sid: str, body: dict = Body(default={})):
    if "fronted" in body:          # S11 confirm fronted
        S.set_fronted(sid, body["fronted"])
    if "person_id" in body:        # S13 approve transfer
        S.approve_transfer(sid, body["person_id"])
    return {"ok": True}
