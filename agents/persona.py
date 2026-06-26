"""Persona agent — represents one friend, emits a stance on a candidate plan.

Owner: Jaydon. TODO Phase 2: derive the stance from the persona's real
constraints (propose / object / concede / accept).
"""


def stance(persona: dict, plan: dict, round_no: int = 1) -> dict:
    """Return a negotiation message (Build Guide §2). Stub: everyone accepts."""
    return {
        "round": round_no,
        "agent": persona["id"],
        "stance": "accept",
        "claim": f"{persona['name']} is good with this",
        "targets_plan": plan.get("plan_id", "PLAN-1"),
        "constraint_ref": None,
    }
