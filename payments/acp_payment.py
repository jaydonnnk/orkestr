"""ACP Delegate Payment API client with Stripe test-mode fallback."""

import logging
import os
import time
from uuid import uuid4

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency safety
    load_dotenv = None

ACP_API_VERSION = "2026-04-17"
LOGGER = logging.getLogger(__name__)


def _created() -> int:
    return int(time.time())


def _headers() -> dict:
    return {
        "Authorization": "Bearer stripe_test_or_mock",
        "Idempotency-Key": str(uuid4()),
        "API-Version": ACP_API_VERSION,
    }


def _mock_token(allowance: dict) -> dict:
    token = {
        "id": "vt_mock_" + uuid4().hex[:12],
        "created": _created(),
        "allowance": allowance,
        "mode": "mock",
        "headers": _headers(),
    }
    LOGGER.info("ACP delegate payment mode=mock")
    return token


def _minor_units(amount) -> int:
    try:
        return max(0, int(round(float(amount) * 100)))
    except (TypeError, ValueError):
        return 0


def delegate_payment(allowance, card=None) -> dict:
    """Create a delegated payment token, using Stripe test mode when available."""
    allowance = allowance or {}
    if load_dotenv:
        load_dotenv()

    secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret_key.startswith("sk_test_"):
        return _mock_token(allowance)

    try:
        import stripe

        stripe.api_key = secret_key
        payment_method = card or "pm_card_visa"
        payment_intent = stripe.PaymentIntent.create(
            amount=_minor_units(allowance.get("max_amount")),
            currency=str(allowance.get("currency", "SGD")).lower(),
            payment_method=payment_method,
            payment_method_types=["card"],
            confirm=True,
            capture_method="manual",
            metadata={
                "merchant_id": str(allowance.get("merchant_id", "")),
                "checkout_session_id": str(allowance.get("checkout_session_id", "")),
                "expires_at": str(allowance.get("expires_at", "")),
                "max_amount": str(allowance.get("max_amount", "")),
                "reason": str(allowance.get("reason", "")),
            },
        )
        token = {
            "id": "vt_" + payment_intent.id,
            "created": _created(),
            "allowance": allowance,
            "stripe_payment_intent": payment_intent.id,
            "mode": "stripe_test",
            "headers": _headers(),
        }
        LOGGER.info("ACP delegate payment mode=stripe_test")
        return token
    except Exception as exc:
        LOGGER.warning("ACP delegate payment falling back to mock: %s", exc.__class__.__name__)
        token = _mock_token(allowance)
        token["stripe_error"] = exc.__class__.__name__
        return token
