"""Convener agent — the orchestrator. Owner: Jaydon.

Generates candidate plans, runs the negotiation, strikes the booking with the
Venue agent, and co-signs the AP2 mandate. Seeded for the demo; swap the seeds
for real constraint-driven rounds in Phase 2.
"""
from agents import venue as venue_agent
from payments.mandate import cosign


def generate_candidates(personas: list, venues: list) -> list:
    """LLM turns freeform prefs -> candidate plans (TODO Phase 2: ai/plan_gen.py)."""
    return [{
        "plan_id": "PLAN-1",
        "title": "Korean BBQ + arcade",
        "day": "FRI",
        "time": "19:30",
        "venue": {"name": "Seoul Garden", "address": "VivoCity #03-01",
                  "lat": 1.3010, "lng": 103.8480, "tags": ["halal", "vegetarian"]},
        "activity": {"name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222},
        "total_cost": 400,
        "per_person": 80,
        "booking_ref": "SG-2026-0627-77",
        "mandate_status": "co-signed",
        "satisfies": [p["id"] for p in personas],
        "conflicts": [],
    }]


def run_negotiation(candidates: list, personas: list) -> dict:
    """Seeded 3 -> 1 narrative so the negotiation ring looks alive (Act 1).

    TODO Phase 2: generate these rounds from each persona's real constraints.
    """
    plan = candidates[0] if candidates else {}
    messages = [
        {"round": 1, "agent": "P-001", "stance": "propose", "claim": "Sushi Hiro on Saturday?", "targets_plan": "PLAN-3", "constraint_ref": None},
        {"round": 1, "agent": "P-003", "stance": "object", "claim": "Carol can't do Saturday — Friday only", "targets_plan": "PLAN-3", "constraint_ref": "available_days"},
        {"round": 1, "agent": "P-002", "stance": "object", "claim": "$70/head blows Bob's $40 cap", "targets_plan": "PLAN-3", "constraint_ref": "budget_max"},
        {"round": 2, "agent": "P-001", "stance": "propose", "claim": "Friday then — Veggie Table?", "targets_plan": "PLAN-2", "constraint_ref": None},
        {"round": 2, "agent": "P-004", "stance": "object", "claim": "Dave wants real meat, not all-veg", "targets_plan": "PLAN-2", "constraint_ref": "dietary"},
        {"round": 3, "agent": "P-001", "stance": "propose", "claim": "Seoul Garden — halal, veg sides, meat, arcade next door", "targets_plan": "PLAN-1", "constraint_ref": None},
        {"round": 3, "agent": "P-005", "stance": "accept", "claim": "Halal and walkable — Eve's in", "targets_plan": "PLAN-1", "constraint_ref": "dietary"},
        {"round": 3, "agent": "P-002", "stance": "accept", "claim": "$48/head works for Bob", "targets_plan": "PLAN-1", "constraint_ref": "budget_max"},
        {"round": 3, "agent": "P-003", "stance": "accept", "claim": "Veg options + arcade — Carol's happy", "targets_plan": "PLAN-1", "constraint_ref": None},
        {"round": 3, "agent": "P-004", "stance": "accept", "claim": "Meat's good — Dave's in", "targets_plan": "PLAN-1", "constraint_ref": None},
    ]
    return {"plan": plan, "messages": messages}


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
        "items": [{"desc": "KBBQ set · table of 5 · FRI 19:30", "amount": response["price_total"]}],
        "booking_ref": "SG-2026-0627-77",
    }
    mandate = cosign(cart, plan["venue"]["name"])
    return {"request": request, "response": response, "mandate": mandate}
