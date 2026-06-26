"""Venue agent — THE OTHER SIDE of the handshake. Owner: Lucas.

Checks availability against venue attributes, quotes/counters terms, signs the cart.
Currently returns seeded responses; wire the real matching logic in Phase 2.
"""
import json
import os

_VENUES = None


def _load():
    global _VENUES
    if _VENUES is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "venues.json")
        with open(path) as f:
            _VENUES = json.load(f)
    return _VENUES


def check_availability(request: dict) -> dict:
    """Match request['needs'] against venue attributes and quote terms.

    TODO Phase 2: real matching over _load(). For now: seeded response
    (7pm is full -> the venue counters 7:30).
    """
    return {
        "available": True,
        "time_offered": "19:30",
        "price_total": 240,
        "per_head": 48,
        "meets": ["halal", "vegetarian_option"],
        "hold_id": "HOLD-77",
    }


def sign_cart(cart: dict, merchant: str = "Seoul Garden") -> str:
    from payments.mandate import sign_cart as _sign
    return _sign(cart, merchant)
