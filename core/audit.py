"""Append-only audit log. Owner: Lucas.

Writes every plan, handshake, mandate, and transfer to audit.jsonl at the repo root.
"""
import json
import os
import time

_LOG = os.path.join(os.path.dirname(__file__), "..", "audit.jsonl")


def record(event: str, payload: dict) -> None:
    with open(_LOG, "a") as f:
        f.write(json.dumps({"ts": time.time(), "event": event, "payload": payload}) + "\n")
