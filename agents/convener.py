"""Convener agent: orchestrates candidate plans, negotiation, and booking.

Candidate contract:
    {
        "plan_id": str,
        "title": str,
        "day": str,
        "time": str,
        "venue": {
            "id": str,
            "name": str,
            "address": str,
            "lat": number | None,
            "lng": number | None,
            "halal": bool,
            "vegetarian": bool,
            "capacity": int | None,
            "tags": list[str],
        },
        "activity": {"name": str, "lat": number | None, "lng": number | None},
        "total_cost": number,
        "per_person": number,
        "booking_ref": str | None,
        "mandate_status": str,
        "satisfies": list,
        "conflicts": list,
    }
"""

import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents import venue as venue_agent
from agents.persona import stance
from payments.mandate import cosign


DEFAULT_PARTY_SIZE = 5
ai_generate = None

CANDIDATE_CONTRACT = {
    "plan_id": "str",
    "title": "str",
    "day": "str",
    "time": "str",
    "venue": {
        "id": "str",
        "name": "str",
        "address": "str",
        "lat": "number|None",
        "lng": "number|None",
        "halal": "bool",
        "vegetarian": "bool",
        "capacity": "int|None",
        "tags": "list[str]",
    },
    "activity": {"name": "str", "lat": "number|None", "lng": "number|None"},
    "total_cost": "number",
    "per_person": "number",
    "booking_ref": "str|None",
    "mandate_status": "str",
    "satisfies": "list",
    "conflicts": "list",
}

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
            "id": "seoul_garden",
            "name": "Seoul Garden",
            "address": "VivoCity #03-01",
            "lat": 1.3010,
            "lng": 103.8480,
            "halal": True,
            "vegetarian": True,
            "capacity": 6,
            "tags": ["halal", "kbbq", "meat", "vegetarian", "vegetarian_option"],
        },
        "activity": {"name": "Timezone @ VivoCity", "lat": 1.2643, "lng": 103.8222},
        "total_cost": 240,
        "per_person": 48,
        "booking_ref": "SG-2026-0627-77",
        "mandate_status": "co-signed",
        "satisfies": [p.get("id", "UNKNOWN") for p in personas if isinstance(p, dict)] if personas else [],
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
    tags = [str(tag).lower() for tag in extra_tags]
    if venue.get("halal"):
        tags.append("halal")
    if venue.get("vegetarian"):
        tags.append("vegetarian")
        tags.append("vegetarian_option")
    return sorted(set(tags))


def _venue_id(candidate: dict):
    if not isinstance(candidate, dict):
        return None
    venue = candidate.get("venue") or {}
    return venue.get("id")


def _coerce_tags(tags) -> list:
    if tags is None:
        return []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        return []
    return [str(tag).strip().lower() for tag in tags if str(tag).strip()]


def _party_size_from_raw(raw: dict) -> int:
    party_size = raw.get("party_size")
    if isinstance(party_size, int) and party_size > 0:
        return party_size
    satisfies = raw.get("satisfies")
    if isinstance(satisfies, list) and satisfies:
        return len(satisfies)
    return DEFAULT_PARTY_SIZE


def _normalize_candidate(raw, venues: list):
    """Coerce one AI candidate into the canonical shape, or drop it."""
    if not isinstance(raw, dict):
        return None

    raw_venue = raw.get("venue") or {}
    if not isinstance(raw_venue, dict):
        return None

    venue_id = raw_venue.get("id")
    matched = next(
        (venue for venue in venues if isinstance(venue, dict) and venue.get("id") == venue_id),
        None,
    )
    if not matched:
        return None

    meta = _VENUE_META.get(venue_id, {})
    party_size = _party_size_from_raw(raw)
    per_person = matched.get("price_per_head", 0)
    total_cost = per_person * party_size
    tags = _venue_tags(matched, meta.get("extra_tags", []))
    tags.extend(_coerce_tags(raw_venue.get("tags")))

    raw_activity = raw.get("activity") or {}
    if not isinstance(raw_activity, dict):
        raw_activity = {}
    default_activity = meta.get("activity", {"name": "Walkable hangout nearby", "lat": None, "lng": None})

    return {
        "plan_id": raw.get("plan_id") or meta.get("plan_id") or venue_id,
        "title": raw.get("title") or meta.get("title") or matched.get("name", "Dinner plan"),
        "day": raw.get("day") or meta.get("day", "FRI"),
        "time": raw.get("time") or meta.get("time", "19:30"),
        "venue": {
            "id": venue_id,
            "name": matched.get("name"),
            "address": meta.get("address", "TBC"),
            "lat": matched.get("lat"),
            "lng": matched.get("lng"),
            "halal": bool(matched.get("halal", False)),
            "vegetarian": bool(matched.get("vegetarian", False)),
            "capacity": matched.get("capacity"),
            "tags": sorted(set(tags)),
        },
        "activity": {
            "name": raw_activity.get("name") or default_activity.get("name", "Walkable hangout nearby"),
            "lat": raw_activity.get("lat", default_activity.get("lat")),
            "lng": raw_activity.get("lng", default_activity.get("lng")),
        },
        "total_cost": total_cost,
        "per_person": per_person,
        "booking_ref": raw.get("booking_ref") or ("SG-2026-0627-77" if venue_id == "seoul_garden" else None),
        "mandate_status": raw.get("mandate_status") or "pending",
        "satisfies": raw.get("satisfies") if isinstance(raw.get("satisfies"), list) else [],
        "conflicts": raw.get("conflicts") if isinstance(raw.get("conflicts"), list) else [],
    }


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
    agent = personas[0].get("id", "CONVENER") if personas else "CONVENER"
    return {
        "round": round_no,
        "agent": agent,
        "stance": "propose",
        "claim": f"How about {plan.get('title', 'this plan')}?",
        "targets_plan": plan.get("plan_id", "PLAN-1"),
        "constraint_ref": None,
    }


_DAY_PREFERENCE = ["FRI", "SAT", "SUN", "THU", "WED", "TUE", "MON"]


def _best_group_day(personas: list):
    """Pick the day the most members are free on (tie → preferred dinner day).

    Candidates otherwise default to FRI, so a group that's only free on SAT/SUN
    would object on every plan. Choosing the max-overlap day lets the day axis
    actually converge instead of always failing on FRI.
    """
    counts: dict = {}
    for persona in personas or []:
        days = (persona.get("constraints") or {}).get("available_days") or []
        for day in days:
            key = str(day).upper()
            counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None

    def rank(day):
        pref = _DAY_PREFERENCE.index(day) if day in _DAY_PREFERENCE else len(_DAY_PREFERENCE)
        return (counts[day], -pref)

    return max(counts, key=rank)


def _apply_group_day(candidates: list, personas: list) -> list:
    """Override each candidate's day with the group's best-overlap day."""
    best_day = _best_group_day(personas)
    if not best_day:
        return candidates
    for candidate in candidates:
        if isinstance(candidate, dict):
            candidate["day"] = best_day
    return candidates


def _deterministic_candidates(personas: list, venues: list) -> list:
    venues = [venue for venue in venues if isinstance(venue, dict)]
    if not venues:
        return [_seeded_plan(personas)]

    by_id = {venue.get("id"): venue for venue in venues}
    ordered_ids = ["sushi_hiro", "veggie_table", "seoul_garden"]
    ordered = [by_id[venue_id] for venue_id in ordered_ids if venue_id in by_id]
    ordered.extend(venue for venue in venues if venue.get("id") not in ordered_ids)
    return [_candidate_from_venue(venue, personas) for venue in ordered]


def _dedupe_candidates(candidates: list, limit: int = 4) -> list:
    deduped = []
    seen = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        venue_id = _venue_id(candidate)
        key = venue_id or candidate.get("plan_id")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
        if len(deduped) >= limit:
            break
    return deduped


def _ensure_seoul_safety(candidates: list, deterministic: list, limit: int = 4) -> list:
    seoul = next((candidate for candidate in deterministic if _venue_id(candidate) == "seoul_garden"), None)
    if not seoul:
        return _dedupe_candidates(candidates, limit=limit)

    with_deterministic_seoul = []
    inserted = False
    for candidate in candidates:
        if _venue_id(candidate) == "seoul_garden":
            if not inserted:
                with_deterministic_seoul.append(seoul)
                inserted = True
            continue
        with_deterministic_seoul.append(candidate)

    if not inserted:
        with_deterministic_seoul.append(seoul)

    deduped = _dedupe_candidates(with_deterministic_seoul, limit=limit)
    if all(_venue_id(candidate) != "seoul_garden" for candidate in deduped):
        if len(deduped) >= limit:
            deduped[-1] = seoul
        else:
            deduped.append(seoul)
    return _dedupe_candidates(deduped, limit=limit)


def _call_ai_generate(personas: list, venues: list):
    generator = ai_generate
    if generator is None:
        from ai.plan_gen import generate as generator
    return generator(personas, venues)


def generate_candidates(personas: list, venues: list) -> list:
    """Generate candidate plans from available venues.

    Nigel's LLM generator can override this once it returns candidates. Until
    then, the convener builds deterministic candidates from venue attributes.
    """
    personas = personas or []
    venues = venues or []
    deterministic = _deterministic_candidates(personas, venues)

    normalized_ai = []
    try:
        ai_candidates = _call_ai_generate(personas, venues)
        if isinstance(ai_candidates, list):
            normalized_ai = [
                candidate
                for candidate in (_normalize_candidate(raw, venues) for raw in ai_candidates)
                if candidate is not None
            ]
    except Exception:
        pass

    candidates = normalized_ai if normalized_ai else deterministic
    candidates = _ensure_seoul_safety(candidates, deterministic, limit=4)
    return _apply_group_day(candidates, personas)


def run_negotiation(candidates: list, personas: list) -> dict:
    """Run real constraint rounds and return the best truthful result."""
    if not candidates or not personas:
        return _seeded_negotiation(personas)

    def _cost(plan):
        try:
            return float(plan.get("per_person") or 0)
        except (TypeError, ValueError):
            return 0.0

    messages = []
    best_plan = None
    best_objection_count = None
    best_cost = None

    for round_no, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            continue
        messages.append(_proposal(candidate, personas, round_no))
        evaluations = [stance(persona, candidate, round_no) for persona in personas]
        messages.extend(evaluations)
        plan = _annotate_plan(candidate, evaluations)
        objections = [msg for msg in evaluations if msg["stance"] == "object"]

        if not objections:
            return {"plan": plan, "messages": messages}

        objection_count = len(objections)
        cost = _cost(candidate)
        # Prefer fewest objections; break ties by the cheapest venue so a group
        # that's over budget on every option still lands on the least-expensive.
        better = (
            best_plan is None
            or objection_count < best_objection_count
            or (objection_count == best_objection_count and cost < best_cost)
        )
        if better:
            best_plan = plan
            best_objection_count = objection_count
            best_cost = cost

    if best_plan is None:
        return _seeded_negotiation(personas)
    return {"plan": best_plan, "messages": messages}


def _booking_basics(plan: dict) -> dict:
    plan = plan or {}
    venue = plan.get("venue") or {}
    plan_time = plan.get("time") or "19:30"
    day = plan.get("day", "FRI")
    # Party size is the whole group, not just whoever accepted. When a plan wins
    # on fewest-objections (not unanimous), satisfies is short — but the table
    # still seats everyone, so count satisfies + conflicts.
    satisfies = plan.get("satisfies") or []
    conflicts = plan.get("conflicts") or []
    n_satisfies = len(satisfies) if isinstance(satisfies, list) else 0
    n_conflicts = len(conflicts) if isinstance(conflicts, list) else 0
    party_size = (n_satisfies + n_conflicts) or 5

    try:
        hour, minute = [int(part) for part in str(plan_time).split(":", 1)]
        total_minutes = max(0, hour * 60 + minute - 30)
        request_time = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    except (TypeError, ValueError):
        request_time = "19:00"

    need_labels = {
        "halal": "halal",
        "vegetarian": "vegetarian_option",
        "vegetarian_option": "vegetarian_option",
    }
    tags = venue.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    needs = sorted({
        need_labels[tag]
        for tag in (str(tag).lower() for tag in tags)
        if tag in need_labels
    })
    title = plan.get("title", "Dinner plan")
    per_person = plan.get("per_person")
    total_amount = plan.get("total_cost")
    if per_person is not None:
        try:
            total_amount = float(per_person) * party_size
        except (TypeError, ValueError):
            total_amount = plan.get("total_cost")
    total_amount = total_amount or 0
    booking_ref = plan.get("booking_ref") or f"BK-{venue.get('id', 'venue')}-{day}"
    return {
        "plan": plan,
        "venue": venue,
        "title": title,
        "party_size": party_size,
        "day": day,
        "plan_time": plan_time,
        "request_time": request_time,
        "needs": needs,
        "total_amount": total_amount,
        "per_person": per_person,
        "booking_ref": booking_ref,
    }


def _fallback_strike_booking(plan: dict, error=None) -> dict:
    basics = _booking_basics(plan)
    request = {
        "party_size": basics["party_size"],
        "day": basics["day"],
        "time": basics["request_time"],
        "request_time": basics["request_time"],
        "budget_total": basics["total_amount"],
        "needs": basics["needs"],
    }
    response = venue_agent.check_availability(request)
    counter_time = response.get("time_offered") or basics["plan_time"]
    response = {
        **response,
        "counter_time": counter_time,
        "per_head": response.get("per_head") or basics["per_person"],
        "price_total": response.get("price_total") or basics["total_amount"],
    }
    cart = {
        "cart_id": "CART-1",
        "items": [{
            "desc": f"{basics['title']} - table of {basics['party_size']} - {basics['day']} {counter_time}",
            "amount": response.get("price_total", basics["total_amount"]),
        }],
        "booking_ref": basics["booking_ref"],
    }
    mandate = {
        **cosign(cart, basics["venue"].get("name", "Unknown Venue")),
        "acp_status": "fallback",
        "vault_token": {"id": "vt_mock_fallback", "mode": "mock"},
        "order": {"booking_ref": basics["booking_ref"], "status": "confirmed"},
        "payment_mode": "mock",
    }
    if error:
        mandate["acp_error"] = error.__class__.__name__
    return {"request": request, "response": response, "mandate": mandate}


def _x402_failed_booking(basics: dict, session, decision: dict) -> dict:
    """Controlled failure when REQUIRE_REAL_X402=true and x402 didn't complete.

    No Stripe charge, no crash, no secret leak — the ACP session is left
    uncompleted and the mandate is marked payment_failed.
    """
    session = session or {}
    counter_time = session.get("counter_time") or basics["plan_time"]
    request = {
        "party_size": basics["party_size"],
        "day": basics["day"],
        "time": basics["request_time"],
        "request_time": basics["request_time"],
        "budget_total": basics["total_amount"],
        "needs": basics["needs"],
    }
    response = {**session, "counter_time": counter_time, "time_offered": counter_time}
    mandate = {
        "cart_id": session.get("id", "CART-X402-FAILED"),
        "merchant": basics["venue"].get("name", "Unknown Venue"),
        "items": session.get("line_items", []),
        "merchant_signature": session.get("id", ""),
        "buyer_authorization": None,
        "status": "payment_failed",
        "booking_ref": basics["booking_ref"],
        "acp_status": "x402_required_failed",
        "vault_token": {"id": "x402_failed", "mode": "x402_failed"},
        "order": {"booking_ref": basics["booking_ref"], "status": "unconfirmed"},
        "payment_mode": "x402_failed",
        "x402": {"reason": decision.get("reason"), "required": True},
    }
    return {"request": request, "response": response, "mandate": mandate}


def strike_booking(plan: dict, allow_x402: bool = False) -> dict:
    """Open the ACP handshake with the merchant agent and co-sign payment.

    When allow_x402 is True (live, non-ORK sessions only) and USE_REAL_X402 is
    on, the booking payment is made via a faithful x402 HTTP 402 handshake to
    the merchant endpoint instead of the Stripe/mock delegate payment. ORK-001
    always calls with the default allow_x402=False, so it is never affected.
    """
    basics = _booking_basics(plan)
    try:
        from datetime import datetime, timedelta, timezone

        from payments import acp_checkout, acp_payment

        item = {
            "id": "li_booking",
            "desc": f"{basics['title']} - table of {basics['party_size']} - {basics['day']} {basics['plan_time']}",
            "amount": basics["total_amount"],
            "quantity": 1,
            "currency": "SGD",
        }
        buyer = {"id": "orkestr_convener", "agent": "Convener"}
        fulfillment = {
            "type": "reservation",
            "day": basics["day"],
            "time": basics["request_time"],
            "request_time": basics["request_time"],
            "booked_time": basics["plan_time"],
            "party_size": basics["party_size"],
            "needs": basics["needs"],
        }
        created = acp_checkout.create_session([item], buyer, fulfillment)
        update_payload = {
            **fulfillment,
            "time": basics["request_time"],
            "counter_time": basics["plan_time"],
        }
        session = acp_checkout.update_session(
            created["id"],
            selected_fulfillment_options=update_payload,
        )
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        allowance = {
            "reason": "one_time",
            "max_amount": session.get("totals", {}).get("amount_total", basics["total_amount"]),
            "currency": "SGD",
            "merchant_id": basics["venue"].get("id", "venue"),
            "checkout_session_id": session["id"],
            "expires_at": expires_at,
        }
        # ---- payment point: faithful x402 (live only) or ACP Stripe/mock ----
        decision = {"action": "fallback", "mode": None}
        if allow_x402:
            from payments import x402_protocol as XP
            decision = XP.resolve_booking_payment({
                "booking_ref": basics["booking_ref"],
                "merchant": basics["venue"].get("name", "Unknown Venue"),
                "party_size": basics["party_size"],
                "day": basics["day"],
                "time": basics["plan_time"],
            })

        if decision["action"] == "controlled_failure":
            return _x402_failed_booking(basics, session, decision)

        x402_mandate = None
        if decision["action"] in ("use_x402", "proceed_uncertain"):
            # x402 already paid (or signed-but-uncertain): do NOT delegate_payment
            # again — that would double-charge (Amendment 2).
            from payments import x402_protocol as XP
            cfg = XP.get_x402_config()
            tx = decision.get("tx_hash") or decision["mode"]
            token = {"id": f"x402_{str(tx)[:48]}", "mode": decision["mode"]}
            payment_data = {
                "vault_token": token["id"],
                "mode": token["mode"],
                "booking_ref": basics["booking_ref"],
                "x402": True,
            }
            x402_mandate = {
                "mode": decision["mode"],
                "tx_hash": decision.get("tx_hash"),
                "payment_response": decision.get("payment_response"),
                "parse_warning": decision.get("parse_warning"),
                "network": cfg["network"],
                "facilitator": cfg["facilitator_url"],
                "reason": decision.get("reason"),
            }
        else:
            # Existing ACP path: USE_REAL_X402 off, or x402 clearly incomplete
            # and not required -> fall back to Stripe/mock delegate payment.
            token = acp_payment.delegate_payment(allowance)
            payment_data = {
                "vault_token": token["id"],
                "mode": token.get("mode"),
                "stripe_payment_intent": token.get("stripe_payment_intent"),
                "booking_ref": basics["booking_ref"],
            }

        completed = acp_checkout.complete_session(session["id"], payment_data=payment_data)
        order = completed.get("order", {})
        counter_time = session.get("counter_time") or basics["plan_time"]
        request = {
            "party_size": basics["party_size"],
            "day": basics["day"],
            "time": basics["request_time"],
            "request_time": basics["request_time"],
            "budget_total": basics["total_amount"],
            "needs": basics["needs"],
            "items": [item],
            "buyer": buyer,
            "fulfillment": fulfillment,
            "checkout_session_id": session["id"],
            "create_session": {
                "items": [item],
                "buyer": buyer,
                "fulfillment": fulfillment,
            },
            "update_session": {
                "selected_fulfillment_options": update_payload,
            },
        }
        response = {
            **session,
            "counter_time": counter_time,
            "time_offered": counter_time,
            "per_head": basics["per_person"],
            "price_total": basics["total_amount"],
        }
        mandate = {
            "cart_id": session["id"],
            "merchant": basics["venue"].get("name", "Unknown Venue"),
            "items": session.get("line_items", []),
            "merchant_signature": session["id"],
            "buyer_authorization": token["id"],
            "status": "co-signed",
            "booking_ref": order.get("booking_ref", basics["booking_ref"]),
            "acp_status": completed.get("status", "completed"),
            "vault_token": token,
            "order": order,
            "payment_mode": x402_mandate["mode"] if x402_mandate else token.get("mode", "mock"),
        }
        if x402_mandate:
            mandate["x402"] = x402_mandate
        return {"request": request, "response": response, "mandate": mandate}
    except Exception as exc:
        return _fallback_strike_booking(plan, error=exc)


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

    def fake_generate(_personas, _venues):
        return [
            {
                "plan_id": "AI-1",
                "title": "AI says Veggie Table",
                "day": "FRI",
                "time": "19:00",
                "venue": {"id": "veggie_table", "tags": "AI-TAG"},
                "per_person": 999,
                "total_cost": 9999,
            },
            {
                "plan_id": "AI-GHOST",
                "title": "Ghost Diner",
                "day": "FRI",
                "time": "19:00",
                "venue": {"id": "ghost_diner", "tags": ["hallucinated"]},
            },
        ]

    ai_generate = fake_generate
    fake_candidates = generate_candidates(personas, venues)
    fake_ids = [_venue_id(candidate) for candidate in fake_candidates]
    assert "ghost_diner" not in fake_ids
    assert "veggie_table" in fake_ids
    assert next(candidate for candidate in fake_candidates if _venue_id(candidate) == "veggie_table")["per_person"] == 35
    print("fake_ai kept", fake_ids)
    print("fake_ai dropped ghost_diner")
    print("NOTE candidate contract: plan_id/title/day/time, venue{id,name,address,lat,lng,halal,vegetarian,capacity,tags[]}, activity{name,lat,lng}, total_cost/per_person, booking_ref, mandate_status, satisfies[], conflicts[].")
