"""LLM: freeform preferences -> structured candidate plans. Owner: Nigel.

Uses OpenAI / Codex (credits provided). Evidence-bound: never invent a constraint.
TODO Phase 2: implement. Keep OPENAI_API_KEY in .env (see .env.example).
"""


def generate(personas: list, venues: list) -> list:
    """Return a list of candidate plan dicts (Build Guide §2). Stub for now."""
    # from openai import OpenAI
    # client = OpenAI()
    # prompt over [p["freeform"] for p in personas] + venue attributes
    # return parsed candidate plans
    return []
