"""ACP checkout mock for the merchant-hosted Agentic Checkout API.

Seoul Garden does not have a live ACP merchant server for the demo, so this
module keeps an in-process merchant that follows the checkout object shapes.
"""

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

ACP_API_VERSION = "2026-04-17"
_SESSIONS = {}


def _headers() -> dict:
    return {
        "Authorization": "Bearer mock_merchant",
        "Idempotency-Key": str(uuid4()),
        "API-Version": ACP_API_VERSION,
        "Timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _line_items(items: list) -> list:
    line_items = []
    for index, item in enumerate(items or [], start=1):
        amount = item.get("amount", 0) if isinstance(item, dict) else 0
        quantity = item.get("quantity", 1) if isinstance(item, dict) else 1
        line_items.append({
            "id": item.get("id", f"li_{index}") if isinstance(item, dict) else f"li_{index}",
            "desc": item.get("desc") if isinstance(item, dict) else "Dinner booking",
            "amount": amount,
            "quantity": quantity,
            "currency": item.get("currency", "SGD") if isinstance(item, dict) else "SGD",
        })
    return line_items


def _totals(line_items: list) -> dict:
    currency = line_items[0].get("currency", "SGD") if line_items else "SGD"
    return {
        "currency": currency,
        "amount_total": sum(item.get("amount", 0) * item.get("quantity", 1) for item in line_items),
    }


def create_session(items, buyer, fulfillment) -> dict:
    """Create an ACP CheckoutSession in incomplete status."""
    session_id = "cs_" + uuid4().hex[:16]
    line_items = _line_items(items)
    session = {
        "id": session_id,
        "status": "incomplete",
        "line_items": line_items,
        "totals": _totals(line_items),
        "fulfillment_options": [fulfillment or {}],
        "messages": [],
        "buyer": buyer or {},
        "payment_data": None,
        "headers": _headers(),
    }
    _SESSIONS[session_id] = session
    return deepcopy(session)


def update_session(session_id, selected_fulfillment_options=None, **updates) -> dict:
    """Update the checkout session and counter the requested time."""
    session = _SESSIONS[session_id]
    selected = selected_fulfillment_options or {}
    request_time = selected.get("request_time") or selected.get("time")
    counter_time = selected.get("booked_time") or selected.get("counter_time") or request_time
    day = selected.get("day")
    party_size = selected.get("party_size")

    fulfillment = {
        **selected,
        "type": "reservation",
        "day": day,
        "time": counter_time,
        "request_time": request_time,
        "counter_time": counter_time,
        "party_size": party_size,
        "status": "offered",
    }
    message = {
        "type": "info",
        "code": "time_adjusted",
        "text": f"{request_time} unavailable - offering {counter_time}",
    }
    session.update(updates)
    session.update({
        "status": "ready_for_payment",
        "fulfillment_options": [fulfillment],
        "messages": session.get("messages", []) + [message],
        "headers": _headers(),
        "request_time": request_time,
        "counter_time": counter_time,
        "time_offered": counter_time,
    })
    return deepcopy(session)


def complete_session(session_id, payment_data) -> dict:
    """Complete an ACP checkout session and return it with an order object."""
    session = _SESSIONS[session_id]
    payment_data = payment_data or {}
    capture = {"status": "not_required"}

    stripe_payment_intent = payment_data.get("stripe_payment_intent")
    if stripe_payment_intent:
        try:
            import os
            import stripe

            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            captured = stripe.PaymentIntent.capture(stripe_payment_intent)
            capture = {"status": "captured", "payment_intent": captured.id}
        except Exception as exc:
            capture = {"status": "capture_skipped", "error": exc.__class__.__name__}

    booking_ref = payment_data.get("booking_ref") or "BK-" + session_id[-8:].upper()
    order = {
        "id": "ord_" + uuid4().hex[:12],
        "booking_ref": booking_ref,
        "status": "confirmed",
        "capture": capture,
    }
    session.update({
        "status": "completed",
        "payment_data": payment_data,
        "order": order,
        "headers": _headers(),
    })
    return deepcopy(session)
