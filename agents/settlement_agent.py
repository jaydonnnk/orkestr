"""Settlement agent — turns who-fronted-what into the minimal x402 transfer set.

Owner: Jaydon. Uses the REAL algorithm in core/settlement.py + the x402 mock.
"""
from core.settlement import compute_net, simplify
from payments.x402 import settle


def build_settlement(fronted: dict, shares: dict) -> dict:
    net = compute_net(fronted, shares)
    transfers = settle(simplify(net))  # x402 mock stamps tx_hash + latency
    return {
        "fronted": fronted,
        "shares": shares,
        "net": net,
        "transfers": transfers,
        "net_after": {p: 0 for p in net},
    }
