"""Settlement math — net balances + minimal-transfer debt simplification.

This is the REAL algorithm (Build Guide §8). No stubs here — it works as-is.
"""


def compute_net(fronted: dict, shares: dict) -> dict:
    """net = paid - owed, per person. Sums to ~0."""
    people = set(fronted) | set(shares)
    return {p: fronted.get(p, 0) - shares.get(p, 0) for p in people}


def simplify(net: dict) -> list:
    """Greedy min-cash-flow: match the biggest debtor to the biggest creditor."""
    cred = sorted(([p, v] for p, v in net.items() if v > 0), key=lambda x: -x[1])
    deb = sorted(([p, -v] for p, v in net.items() if v < 0), key=lambda x: -x[1])
    transfers, i, j = [], 0, 0
    while i < len(deb) and j < len(cred):
        amt = min(deb[i][1], cred[j][1])
        transfers.append({"from": deb[i][0], "to": cred[j][0], "amount": amt})
        deb[i][1] -= amt
        cred[j][1] -= amt
        if deb[i][1] == 0:
            i += 1
        if cred[j][1] == 0:
            j += 1
    return transfers
