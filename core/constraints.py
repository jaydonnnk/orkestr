"""Constraint satisfaction — score candidate plans against all personas.

Owner: Jaydon. TODO Phase 2: real scoring (day overlap, budget ceiling,
dietary match, travel limit, near-arcade).
"""


def satisfies(plan: dict, persona: dict) -> bool:
    """TODO Phase 2: real per-constraint check. Stub returns True."""
    return True


def score_plan(plan: dict, personas: list) -> int:
    """Higher = more people satisfied."""
    return sum(1 for p in personas if satisfies(plan, p))


def best_plan(candidates: list, personas: list) -> dict:
    """Pick the max-satisfaction candidate."""
    if not candidates:
        return {}
    return max(candidates, key=lambda c: score_plan(c, personas))
