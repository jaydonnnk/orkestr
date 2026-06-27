"""Persona agent: represents one friend and evaluates a candidate plan.

Owner: Jaydon. Each stance is evidence-bound to the persona's submitted
constraints so the negotiation ring can show real objections instead of a
script-only story.
"""


def _plan_text(plan: dict) -> str:
    venue = plan.get("venue") or {}
    activity = plan.get("activity") or {}
    bits = [
        plan.get("title", ""),
        venue.get("name", ""),
        " ".join(venue.get("tags", [])),
        activity.get("name", ""),
    ]
    return " ".join(str(bit).lower() for bit in bits if bit)


def _venue_supports(plan: dict, need: str) -> bool:
    venue = plan.get("venue") or {}
    tags = {str(tag).lower() for tag in venue.get("tags", [])}
    if need == "vegetarian":
        return bool(venue.get("vegetarian")) or "vegetarian" in tags or "vegetarian_option" in tags
    if need == "halal":
        return bool(venue.get("halal")) or "halal" in tags
    if need == "no_raw_fish":
        text = _plan_text(plan)
        return "raw" not in text and "sushi" not in text and "sashimi" not in text
    return True


def _dietary_objection(persona: dict, plan: dict):
    constraints = persona.get("constraints") or {}
    dietary = constraints.get("dietary") or []
    for need in dietary:
        if not _venue_supports(plan, need):
            return need

    # Soft preference from the demo data: Dave asked for meat, so an all-veg
    # venue should not look like a perfect consensus choice.
    freeform = persona.get("freeform", "").lower()
    tags = {str(tag).lower() for tag in (plan.get("venue") or {}).get("tags", [])}
    if "meat" in freeform and ("all_veg" in tags or "vegetarian_only" in tags):
        return "meat_preference"

    return None


def stance(persona: dict, plan: dict, round_no: int = 1) -> dict:
    """Return this persona's stance on the proposed plan."""
    constraints = persona.get("constraints") or {}
    agent_id = persona.get("id", "UNKNOWN")
    name = persona.get("name", agent_id)
    plan_id = plan.get("plan_id", "PLAN-1")

    available_days = constraints.get("available_days") or []
    day = plan.get("day")
    if available_days and day not in available_days:
        return {
            "round": round_no,
            "agent": agent_id,
            "stance": "object",
            "claim": f"{name} cannot do {day}; available days: {', '.join(available_days)}",
            "targets_plan": plan_id,
            "constraint_ref": "available_days",
        }

    budget_max = constraints.get("budget_max")
    per_person = plan.get("per_person")
    if budget_max is not None and per_person is not None and per_person > budget_max:
        return {
            "round": round_no,
            "agent": agent_id,
            "stance": "object",
            "claim": f"${per_person}/head is over {name}'s ${budget_max} cap",
            "targets_plan": plan_id,
            "constraint_ref": "budget_max",
        }

    dietary_issue = _dietary_objection(persona, plan)
    if dietary_issue:
        labels = {
            "vegetarian": "vegetarian options",
            "halal": "halal food",
            "no_raw_fish": "no raw fish",
            "meat_preference": "a meat option",
        }
        return {
            "round": round_no,
            "agent": agent_id,
            "stance": "object",
            "claim": f"{name} needs {labels.get(dietary_issue, dietary_issue)}",
            "targets_plan": plan_id,
            "constraint_ref": "dietary",
        }

    return {
        "round": round_no,
        "agent": agent_id,
        "stance": "accept",
        "claim": f"{name} accepts: day, budget, and dietary needs fit",
        "targets_plan": plan_id,
        "constraint_ref": None,
    }
