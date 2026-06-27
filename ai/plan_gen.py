"""LLM: freeform preferences -> structured candidate plans. Owner: Nigel.

Evidence-bound: the LLM only ever RANKS the real venues from data/venues.json
against everyone's real freeform notes/constraints. It never invents a venue,
price, or constraint - every field on the returned plan dicts comes straight
from the data file. If the OpenAI call is unavailable (no key, network, bad
response) we fall back to a deterministic ranking so the convener always gets
a usable candidate list.

Return shape matches agents/convener.py's candidate dicts (Build Guide §2),
so Jaydon's generate_candidates() can use this output directly.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_DAY = "FRI"
_DEFAULT_TIME = "19:30"


def _venue_tags(venue: dict) -> list:
    tags = []
    if venue.get("halal"):
        tags.append("halal")
    if venue.get("vegetarian"):
        tags.extend(["vegetarian", "vegetarian_option"])
    return sorted(set(tags))


def _candidate_from_venue(venue: dict, personas: list) -> dict:
    """Build a candidate plan dict using only fields present on `venue`."""
    party_size = len(personas) or 5
    per_person = venue.get("price_per_head", 0)
    return {
        "plan_id": str(venue.get("id", "plan")).upper(),
        "title": f"Dinner at {venue.get('name', 'TBC')}",
        "day": _DEFAULT_DAY,
        "time": _DEFAULT_TIME,
        "venue": {
            "id": venue.get("id"),
            "name": venue.get("name"),
            "address": "TBC",
            "lat": venue.get("lat"),
            "lng": venue.get("lng"),
            "halal": venue.get("halal", False),
            "vegetarian": venue.get("vegetarian", False),
            "capacity": venue.get("capacity"),
            "tags": _venue_tags(venue),
        },
        "activity": {"name": "Walkable hangout nearby"} if not venue.get("near_arcade") else {"name": "Arcade nearby"},
        "total_cost": per_person * party_size,
        "per_person": per_person,
        "booking_ref": None,
        "mandate_status": "pending",
        "satisfies": [],
        "conflicts": [],
    }


def _fit_score(venue: dict, personas: list) -> int:
    """Deterministic fallback ranking: how many people's stated constraints
    this venue satisfies on price and dietary needs (no LLM involved)."""
    score = 0
    for p in personas:
        constraints = p.get("constraints") or {}
        budget_max = constraints.get("budget_max")
        if budget_max is None or venue.get("price_per_head", 0) <= budget_max:
            score += 1
        for need in constraints.get("dietary") or []:
            if need == "vegetarian" and not venue.get("vegetarian"):
                score -= 1
            if need == "halal" and not venue.get("halal"):
                score -= 1
            if need == "no_raw_fish" and "sushi" in venue.get("name", "").lower():
                score -= 1
    return score


def _fallback_order(personas: list, venues: list) -> list:
    return sorted(venues, key=lambda v: _fit_score(v, personas), reverse=True)


def _rank_with_llm(personas: list, venues: list) -> list:
    """Ask the LLM to order venue ids best-fit-first. Returns an ordered list
    of venue dicts drawn only from `venues`, or raises on any failure so the
    caller can fall back."""
    from openai import OpenAI

    client = OpenAI()
    by_id = {v["id"]: v for v in venues}
    notes = "\n".join(f"- {p.get('name')}: {p.get('freeform', '')}" for p in personas)
    venue_summary = "\n".join(
        f"- {v['id']}: halal={v.get('halal')}, vegetarian={v.get('vegetarian')}, "
        f"price_per_head={v.get('price_per_head')}, near_arcade={v.get('near_arcade')}"
        for v in venues
    )
    prompt = (
        "Rank these venues best-fit-first for the group below, using only the "
        "facts listed - do not invent venues, prices, or needs not stated.\n\n"
        f"People's freeform notes:\n{notes}\n\n"
        f"Venues:\n{venue_summary}\n\n"
        "Respond with JSON only: {\"ranking\": [\"<venue_id>\", ...]} "
        f"using exactly the ids {list(by_id)}, every id included once."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response.choices[0].message.content)
    ranking = [vid for vid in parsed.get("ranking", []) if vid in by_id]
    if not ranking:
        raise ValueError("LLM ranking did not name any known venue id")
    missing = [vid for vid in by_id if vid not in ranking]
    return [by_id[vid] for vid in ranking + missing]


def generate(personas: list, venues: list) -> list:
    """Return a list of candidate plan dicts (Build Guide §2), best fit first.

    Returns [] whenever the LLM didn't actually run (no key, network error,
    bad response) so the convener keeps using its own richer, hand-tuned
    candidates (real addresses, activities, booking_ref) instead of this
    module's generic ones. This module's contribution is the LLM ranking
    itself, not a replacement for that metadata.
    """
    if not venues or not os.environ.get("OPENAI_API_KEY"):
        return []
    try:
        ordered = _rank_with_llm(personas, venues)
    except Exception:
        return []
    return [_candidate_from_venue(venue, personas) for venue in ordered]


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(data_dir, "personas.json")) as f:
        personas = json.load(f)
    with open(os.path.join(data_dir, "venues.json")) as f:
        venues = json.load(f)

    candidates = generate(personas, venues)
    if candidates:
        print("(LLM ranking)")
    else:
        print("(no OPENAI_API_KEY / LLM unavailable - showing fallback heuristic ranking)")
        candidates = [_candidate_from_venue(v, personas) for v in _fallback_order(personas, venues)]
    for plan in candidates:
        print(plan["plan_id"], plan["title"], plan["per_person"])
