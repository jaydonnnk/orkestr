"""AP2-shaped mandate mock. Owner: Jaydon.

The merchant signs the cart FIRST (its price/terms guarantee), then the buyer
authorizes. TODO (production): real AP2 signed mandates (ECDSA P-256).
"""


def sign_cart(cart: dict, merchant: str) -> str:
    """Venue agent signs the cart -> merchant_signature (mock)."""
    return "0xVENUE_" + merchant.replace(" ", "_").upper()[:12]


def authorize(cart_id: str, buyer: str = "convener") -> str:
    """Buyer authorizes payment -> buyer_authorization (mock)."""
    return "0xCONVENER_" + cart_id


def cosign(cart: dict, merchant: str) -> dict:
    """Produce the co-signed mandate (Build Guide §2)."""
    cart_id = cart.get("cart_id", "CART-1")
    return {
        "cart_id": cart_id,
        "merchant": merchant,
        "items": cart.get("items", []),
        "merchant_signature": sign_cart(cart, merchant),
        "buyer_authorization": authorize(cart_id),
        "status": "co-signed",
        "booking_ref": cart.get("booking_ref", "SG-2026-0627-77"),
    }


def verify(mandate: dict) -> bool:
    """Check the cart wasn't tampered after signing.

    Stretch goal (Build Guide §4, Phase 7): the tampered-cart catch.
    """
    return mandate.get("status") == "co-signed"
