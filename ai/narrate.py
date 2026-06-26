"""LLM narration — negotiation lines, venue dialogue, 'Settled' copy. Owner: Nigel.

Narrate ONLY the real constraint_ref; never invent a reason. TODO Phase 2-3.
"""


def negotiation_line(message: dict) -> str:
    """Turn a negotiation message into a human line. Stub passes the claim through."""
    return message.get("claim", "")


def venue_line(handshake: dict) -> str:
    return "Table held — 7pm was full, 7:30 confirmed."


def settled_line() -> str:
    return "Everyone's square. Nobody's chasing anybody."
