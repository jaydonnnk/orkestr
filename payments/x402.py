"""x402 settlement mock. Owner: Lucas.

stamp() returns a fake tx hash for a single settled transfer.
settle() batch-stamps a list. TODO (production): real x402 stablecoin settlement.
"""
import random


def stamp() -> str:
    return "0x%012x" % random.getrandbits(48)


def settle(transfers: list) -> list:
    out = []
    for t in transfers:
        out.append({
            **t,
            "rail": "x402",
            "status": "settled",
            "tx_hash": stamp(),
            "latency_ms": random.randint(800, 1500),
        })
    return out
