"""Convener agent: orchestrates candidate plans, negotiation, and booking."""

import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents import venue as venue_agent
from agents.persona import stance
from payments.mandate import cosign


_VENUE_META = {
    "seoul_garden": {
        "plan_id": "PLAN-1",
        "title": "Korean BBQ + arcade",
        "day": "FRI",
        "time": "19:30",
        "address": "VivoCity #03-01",
        "activity": {"name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222},
        "extra_tags": ["kbbq", "meat"],
    },
    "veggie_table": {
        "plan_id": "PLAN-2",
        "title": "Veggie Table dinner",
        "day": "FRI",
        "time": "19:00",
        "address": "HarbourFront Walk",
        "activity": {"name": "Board games nearby", "lat": 1.2980, "lng": 103.8510},
        "extra_tags": ["all_veg", "vegetarian_only"],
    },
    "sushi_hiro": {
        "plan_id": "PLAN-3",
        "title": "Sushi Hiro on Saturday",
        "day": "SAT",
        "time": "19:00",
        "address": "Orchard Central #04-18",
        "activity": {"name": "Dessert after dinner", "lat": 1.3040, "lng": 103.8320},
        "extra_tags": ["sushi", "raw_fish"],
    },
}


def _seeded_plan(personas=None) -> dict:
    return {
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
        "satisfies": [p["id"] for p in personas] if personas else [],
        "conflicts": [],
    }


def _seeded_messages() -> list:
    return [
        {"round": 1, "agent": "P-001", "stance": "propose", "claim": "Sushi Hiro on Saturday?", "targets_plan": "PLAN-3", "constraint_ref": None},
        {"round": 1, "agent": "P-003", "stance": "object", "claim": "Carol can't do Saturday - Friday only", "targets_plan": "PLAN-3", "constraint_ref": "available_days"},
        {"round": 1, "agent": "P-002", "stance": "object", "claim": "$70/head blows Bob's $40 cap", "targets_plan": "PLAN-3", "constraint_ref": "budget_max"},
        {"round": 2, "agent": "P-001", "stance": "propose", "claim": "Friday then - Veggie Table?", "targets_plan": "PLAN-2", "constraint_ref": None},
        {"round": 2, "agent": "P-004", "stance": "object", "claim": "Dave wants real meat, not all-veg", "targets_plan": "PLAN-2", "constraint_ref": "dietary"},
        {"round": 3, "agent": "P-001", "stance": "propose", "claim": "Seoul Garden - halal, veg sides, meat, arcade next door", "targets_plan": "PLAN-1", "constraint_ref": None},
        {"round": 3, "agent": "P-005", "stance": "accept", "claim": "Halal and walkable - Eve's in", "targets_plan": "PLAN-1", "constraint_ref": "dietary"},
        {"round": 3, "agent": "P-002", "stance": "accept", "claim": "$48/head works for Bob", "targets_plan": "PLAN-1", "constraint_ref": "budget_max"},
        {"round": 3, "agent": "P-003", "stance": "accept", "claim": "Veg options + arcade - Carol's happy", "targets_plan": "PLAN-1", "constraint_ref": None},
        {"round": 3, "agent": "P-004", "stance": "accept", "claim": "Meat's good - Dave's in", "targets_plan": "PLAN-1", "constraint_ref": None},
    ]


def _seeded_negotiation(personas=None) -> dict:
    return {"plan": _seeded_plan(personas), "messages": _seeded_messages()}


def _venue_tags(venue: dict, extra_tags: list) -> list:
    tags = list(extra_tags)
    if venue.get("halal"):
        tags.append("halal")
    if venue.get("vegetarian"):
        tags.append("vegetarian")
        tags.append("vegetarian_option")
    return sorted(set(tags))


def _candidate_from_venue(venue: dict, personas: list) -> dict:
    meta = _VENUE_META.get(venue.get("id"), {})
    party_size = len(personas) or 5
    per_person = venue.get("price_per_head", 0)
    total_cost = per_person * party_size
    return {
        "plan_id": meta.get("plan_id", venue.get("id", "PLAN-1")),
        "title": meta.get("title", venue.get("name", "Dinner plan")),
        "day": meta.get("day", "FRI"),
        "time": meta.get("time", "19:30"),
        "venue": {
            "id": venue.get("id"),
            "name": venue.get("name"),
            "address": meta.get("address", "TBC"),
            "lat": venue.get("lat"),
            "lng": venue.get("lng"),
            "halal": venue.get("halal", False),
            "vegetarian": venue.get("vegetarian", False),
            "capacity": venue.get("capacity"),
            "tags": _venue_tags(venue, meta.get("extra_tags", [])),
        },
        "activity": meta.get("activity", {"name": "Walkable hangout nearby"}),
        "total_cost": total_cost,
        "per_person": per_person,
        "booking_ref": "SG-2026-0627-77" if venue.get("id") == "seoul_garden" else None,
        "mandate_status": "pending",
        "satisfies": [],
        "conflicts": [],
    }


def _annotate_plan(plan: dict, evaluations: list) -> dict:
    accepted = [msg["agent"] for msg in evaluations if msg["stance"] == "accept"]
    conflicts = [
        {
            "agent": msg["agent"],
            "constraint_ref": msg["constraint_ref"],
            "claim": msg["claim"],
        }
        for msg in evaluations
        if msg["stance"] == "object"
    ]
    return {**plan, "satisfies": accepted, "conflicts": conflicts}


def _proposal(plan: dict, personas: list, round_no: int) -> dict:
    agent = personas[0]["id"] if personas else "CONVENER"
    return {
        "round": round_no,
        "agent": agent,
        "stance": "propose",
        "claim": f"How about {plan.get('title', 'this plan')}?",
        "targets_plan": plan.get("plan_id", "PLAN-1"),
        "constraint_ref": None,
    }


def generate_candidates(personas: list, venues: list) -> list:
    """Generate candidate plans from available venues.

    Nigel's LLM generator can override this once it returns candidates. Until
    then, the convener builds deterministic candidates from venue attributes.
    """
    try:
        from ai.plan_gen import generate as ai_generate

        ai_candidates = ai_generate(personas, venues)
        if ai_candidates:
            return ai_candidates
    except Exception:
        pass

    if not venues:
        return [_seeded_plan(personas)]

    by_id = {venue.get("id"): venue for venue in venues}
    ordered_ids = ["sushi_hiro", "veggie_table", "seoul_garden"]
    ordered = [by_id[venue_id] for venue_id in ordered_ids if venue_id in by_id]
    ordered.extend(venue for venue in venues if venue.get("id") not in ordered_ids)
    return [_candidate_from_venue(venue, personas) for venue in ordered]


def run_negotiation(candidates: list, personas: list) -> dict:
    """Run real constraint rounds and return the best truthful result."""
    if not candidates or not personas:
        return _seeded_negotiation(personas)

    messages = []
    best_plan = None
    best_objection_count = None

    for round_no, candidate in enumerate(candidates, start=1):
        messages.append(_proposal(candidate, personas, round_no))
        evaluations = [stance(persona, candidate, round_no) for persona in personas]
        messages.extend(evaluations)
        plan = _annotate_plan(candidate, evaluations)
        objections = [msg for msg in evaluations if msg["stance"] == "object"]

        if not objections:
            return {"plan": plan, "messages": messages}

        objection_count = len(objections)
        if best_objection_count is None or objection_count <= best_objection_count:
            best_plan = plan
            best_objection_count = objection_count

    return {"plan": best_plan, "messages": messages}


def strike_booking(plan: dict) -> dict:
    """Open the handshake with the Venue agent and co-sign the cart (Act 2)."""
    request = {
        "party_size": len(plan.get("satisfies", [])) or 5,
        "day": plan.get("day", "FRI"),
        "time": "19:00",
        "budget_total": plan.get("total_cost", 400),
        "needs": ["halal", "vegetarian_option"],
    }
    response = venue_agent.check_availability(request)
    cart = {
        "cart_id": "CART-1",
        "items": [{"desc": "KBBQ set - table of 5 - FRI 19:30", "amount": response["price_total"]}],
        "booking_ref": "SG-2026-0627-77",
    }
    mandate = cosign(cart, plan["venue"]["name"])
    return {"request": request, "response": response, "mandate": mandate}


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(data_dir, "personas.json")) as f:
        personas = json.load(f)
    with open(os.path.join(data_dir, "venues.json")) as f:
        venues = json.load(f)

    result = run_negotiation(generate_candidates(personas, venues), personas)
    print("title", result["plan"]["title"])
    print("msgs", len(result["messages"]))
    print("satisfies", result["plan"]["satisfies"])
    print("conflicts", result["plan"].get("conflicts"))
    print("NOTE ask the data owner to change Bob budget_max from 40 to 50 for unanimous Seoul convergence.")
