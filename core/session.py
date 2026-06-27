"""In-memory session store + state machine for the full Orkestr webapp.

Seeded with a default demo session (ORK-001) so every screen has data on boot.
Hackathon approach: REAL endpoints, SEEDED data underneath — swap the stubs for
real negotiation/constraint logic per the Build Guide without touching the API.

Owner: Lucas (session plumbing) + Jaydon (the agent calls).
"""
import json
import os
import uuid

from fastapi import HTTPException

from agents.convener import (generate_candidates, run_negotiation, strike_booking,
                             _seeded_messages)
from core.settlement import compute_net, simplify
from payments.x402 import stamp

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SESSIONS = {}
PHASES = ["negotiating", "plan_ready", "booking", "confirmed"]


def _load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def get(sid):
    return SESSIONS.get(sid)


def _members(s):
    return s["members"] or _load("personas.json")


def new_session(name=None, date_range=None):
    sid = "ORK-" + uuid.uuid4().hex[:4].upper()
    SESSIONS[sid] = {
        "session_id": sid,
        "name": name or "Friday plan",
        "date_range": date_range,
        "phase": "negotiating",
        "members": [],
        "negotiation": [],
        "plan": None,
        "handshake": None,
        "approvals": [],
        "expenses": [],
        "settlement": None,
    }
    return SESSIONS[sid]


def new_live_session(name=None, date_range=None):
    """A real (non-seeded) session pre-populated with 5 member *identities* only.

    The group exists from the start (names/avatars), but every constraint is
    entered live and each member must press find-our-plan before the pipeline
    runs. Marked live=True so the status gate waits for all 5 (see all_ready).
    """
    s = new_session(name or "Live plan", date_range)
    shells = []
    for p in _load("personas.json")[:5]:
        shells.append({
            "id": p["id"],
            "name": p.get("name", p["id"]),
            "avatar": p.get("avatar"),
            "constraints": {},
            "freeform": "",
        })
    s["members"] = shells
    s["live"] = True
    s["ready"] = []
    return s


def mark_ready(sid, person_id):
    """Record that one member pressed find-our-plan."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    if not person_id:
        raise HTTPException(status_code=400, detail="person_id required")
    s = SESSIONS[sid]
    if person_id not in [m["id"] for m in s["members"]]:
        raise HTTPException(status_code=400, detail="unknown person_id")
    if person_id not in s.setdefault("ready", []):
        s["ready"].append(person_id)
    return s


def all_ready(s):
    """True once every member of a live session has pressed find-our-plan."""
    member_ids = {m["id"] for m in s.get("members", [])}
    if not member_ids:
        return False
    return member_ids.issubset(set(s.get("ready", [])))


def add_constraints(sid, person):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    if not person.get("id"):
        raise HTTPException(status_code=400, detail="id required")
    s = SESSIONS[sid]
    s["members"] = [m for m in s["members"] if m["id"] != person.get("id")] + [person]
    return s


def compute_plan(sid):
    """Negotiation -> plan -> venue handshake. Moves phase to plan_ready."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    s = SESSIONS[sid]
    members = _members(s)
    venues = _load("venues.json")
    # Exa planning supplement: only for non-ORK sessions when both flags are on.
    # Any Exa failure silently falls back to seeded venues only.
    if sid != "ORK-001":
        try:
            from agents.discovery import exa_venue_supplements
            extra = exa_venue_supplements(members, limit=3)
            if extra:
                venues = venues + extra
        except Exception:
            pass
    candidates = generate_candidates(members, venues)
    neg = run_negotiation(candidates, members)
    s["negotiation"] = neg["messages"]
    s["plan"] = neg["plan"]
    # Quorum: fewer than half the agents could agree (budget / availability /
    # dietary). Don't strike a booking — fail and let the frontend alert the group.
    accepts = len((s["plan"] or {}).get("satisfies") or [])
    needed = (len(members) + 1) // 2
    if neg.get("quorum") is False:
        s["handshake"] = None
        s["booking_failed"] = True
        s["fail_reason"] = (
            f"Only {accepts} of {len(members)} could agree (need {needed}). "
            "No venue fits enough of the group's budget, dates, and dietary needs."
        )
        s["phase"] = "failed"
        return s

    s["booking_failed"] = False
    s["fail_reason"] = None
    # allow_x402 only for live sessions; ORK-001's seed_demo keeps the default
    # allow_x402=False, so the frozen demo never attempts a real x402 payment.
    booking = strike_booking(s["plan"], allow_x402=bool(s.get("live")))
    s["handshake"] = {
        "request": booking["request"],
        "response": booking["response"],
        "mandate": booking["mandate"],
        "booking_ref": booking["mandate"]["booking_ref"],
        "status": booking["mandate"]["status"],
        "merchant": booking["mandate"]["merchant"],
    }
    if s["phase"] in ("negotiating", "failed"):
        s["phase"] = "plan_ready"
    # Live sessions have no seeded expenses, so x402 would have nothing to
    # settle. Treat the venue booking the Convener (first member) struck over
    # ACP as a fronted expense, split evenly — that's what x402 reimburses.
    if s.get("live") and not s.get("_booking_expense_added"):
        members = _members(s)
        total = (s["plan"] or {}).get("total_cost") or 0
        if members and total:
            s["_booking_expense_added"] = True
            add_expense(sid, {
                "paid_by": members[0]["id"],
                "amount": total,
                "description": f"Venue booking — {s['plan'].get('title', 'dinner')}",
                "split": "even",
            })
    return s


def approve_plan(sid, person_id):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    if not person_id:
        raise HTTPException(status_code=400, detail="person_id required")
    s = SESSIONS[sid]
    member_ids = [m["id"] for m in _members(s)]
    if person_id not in member_ids:
        raise HTTPException(status_code=400, detail="unknown person_id")
    if person_id not in s["approvals"]:
        s["approvals"].append(person_id)
    if len(s["approvals"]) >= len(_members(s)):
        s["phase"] = "confirmed"
    elif s["phase"] == "plan_ready":
        s["phase"] = "booking"
    return s


def add_expense(sid, expense):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    s = SESSIONS[sid]
    expense.setdefault("id", "EXP-" + uuid.uuid4().hex[:4])
    s["expenses"].append(expense)
    recompute_settlement(sid)
    return s


def set_fronted(sid, fronted):
    """S11 confirm-fronted: override the fronted map and recompute."""
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    SESSIONS[sid]["_fronted_override"] = fronted
    return recompute_settlement(sid)


def recompute_settlement(sid):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    s = SESSIONS[sid]
    ids = [m["id"] for m in _members(s)]
    if s.get("_fronted_override"):
        fronted = {pid: s["_fronted_override"].get(pid, 0) for pid in ids}
    else:
        fronted = {pid: 0 for pid in ids}
        for e in s["expenses"]:
            fronted[e["paid_by"]] = fronted.get(e["paid_by"], 0) + e["amount"]
    total = sum(fronted.values())
    per = round(total / len(ids)) if ids else 0
    shares = {pid: per for pid in ids}
    net = compute_net(fronted, shares)
    transfers = [
        {**t, "rail": "x402", "status": "pending", "tx_hash": None, "latency_ms": 1000}
        for t in simplify(net)
    ]
    s["settlement"] = {
        "fronted": fronted,
        "shares": shares,
        "net": net,
        "transfers": transfers,
        "net_after": {pid: 0 for pid in ids},
    }
    return s["settlement"]


def approve_transfer(sid, person_id):
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    s = SESSIONS[sid]
    st = s["settlement"] or recompute_settlement(sid)
    for t in st["transfers"]:
        if t["from"] == person_id and t["status"] == "pending":
            t["status"] = "settled"
            t["tx_hash"] = stamp()
    return s


def seed_demo():
    """Pre-populate ORK-001 so the app is fully populated on boot."""
    if "ORK-001" in SESSIONS:
        return
    SESSIONS["ORK-001"] = {
        "session_id": "ORK-001",
        "name": "Friday — the squad",
        "date_range": ["2026-06-26", "2026-06-28"],
        "phase": "negotiating",
        "members": _load("personas.json"),
        "negotiation": [],
        "plan": None,
        "handshake": None,
        "approvals": ["P-001", "P-003", "P-004", "P-005"],
        "expenses": [],
        "settlement": None,
    }
    compute_plan("ORK-001")
    # Pin ORK-001 to frozen demo values.
    # per_person=80 = total expenses (240+100+60=400) / 5 people.
    # _seeded_plan() in convener.py is not used here because its values
    # can change as the agent layer evolves; these numbers are contractually frozen.
    s = SESSIONS["ORK-001"]
    seeded_plan = {
        "plan_id": "PLAN-1",
        "title": "Korean BBQ + arcade",
        "day": "FRI",
        "time": "19:30",
        "venue": {
            "name": "Seoul Garden",
            "address": "VivoCity #03-01",
            "lat": 1.3010,
            "lng": 103.8480,
            "tags": ["halal", "vegetarian"],
        },
        "activity": {"name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222},
        "total_cost": 400,
        "per_person": 80,
        "booking_ref": "SG-2026-0627-77",
        "mandate_status": "co-signed",
        "satisfies": [p["id"] for p in s["members"] if isinstance(p, dict)],
        "conflicts": [],
    }
    booking = strike_booking(seeded_plan)
    s["negotiation"] = _seeded_messages()
    s["plan"] = seeded_plan
    s["handshake"] = {
        "request": booking["request"],
        "response": booking["response"],
        "mandate": booking["mandate"],
        "booking_ref": booking["mandate"]["booking_ref"],
        "status": booking["mandate"]["status"],
        "merchant": booking["mandate"]["merchant"],
    }
    s["phase"] = "plan_ready"
    for e in [
        {"paid_by": "P-001", "amount": 240, "description": "Dinner — KBBQ set", "split": "even"},
        {"paid_by": "P-002", "amount": 100, "description": "Arcade credit", "split": "even"},
        {"paid_by": "P-003", "amount": 60, "description": "Drinks", "split": "even"},
    ]:
        add_expense("ORK-001", e)
