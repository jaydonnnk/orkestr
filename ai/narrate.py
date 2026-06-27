"""LLM narration — negotiation lines, venue dialogue, 'Settled' copy. Owner: Nigel.

Narrate ONLY what's actually on the message/handshake/settlement passed in -
never invent a reason, a price, or a constraint_ref that isn't there.
"""

_STANCE_TAG = {"propose": "PROPOSE", "accept": "ACCEPT", "object": "OBJECT"}


def negotiation_line(message: dict) -> str:
    """Turn one negotiation message into a human line for the ring (Act 1)."""
    claim = message.get("claim", "")
    if not claim:
        return ""
    tag = _STANCE_TAG.get(message.get("stance"))
    return f"[{tag}] {claim}" if tag else claim


def handshake_lines(handshake: dict) -> list:
    """Turn the request/response/mandate into the venue dialogue (Act 2)."""
    if not handshake:
        return []
    request = handshake.get("request") or {}
    response = handshake.get("response") or {}
    mandate = handshake.get("mandate") or {}
    merchant = mandate.get("merchant", "The venue")

    lines = []
    party_size = request.get("party_size")
    day = request.get("day")
    requested_time = request.get("time")
    lines.append(
        f"Your agent asks: table for {party_size} on {day} at {requested_time}."
    )

    offered_time = response.get("time_offered")
    if offered_time and requested_time and offered_time != requested_time:
        lines.append(f"{merchant}'s agent counters: {requested_time} is full, {offered_time} is open.")
    elif offered_time:
        lines.append(f"{merchant}'s agent confirms {offered_time}.")

    if mandate.get("status") == "co-signed":
        booking_ref = mandate.get("booking_ref")
        lines.append(f"Both agents co-sign - booking {booking_ref} is locked in.")

    return lines


def venue_line(handshake: dict) -> str:
    """One-line summary of the handshake, for when there's no room for the
    full dialogue (e.g. a status strip)."""
    lines = handshake_lines(handshake)
    return lines[-1] if lines else "Table held."


def settled_line(settlement: dict = None) -> str:
    """'Settled' copy for Act 3 - reflects the real transfer/net state."""
    if not settlement:
        return "Everyone's square. Nobody's chasing anybody."
    transfers = settlement.get("transfers") or []
    pending = [t for t in transfers if t.get("status") != "settled"]
    net_after = settlement.get("net_after") or {}
    if not pending and all(v == 0 for v in net_after.values()):
        return "Everyone's square. Nobody's chasing anybody."
    n = len(pending)
    return f"{n} transfer{'s' if n != 1 else ''} left before everyone's square."
