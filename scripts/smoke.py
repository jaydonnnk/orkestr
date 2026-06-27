"""Smoke tests for the Orkestr backend hardening.

Stdlib only (urllib.request, json, os, sys). No pytest, no third-party deps.

Usage:
    python scripts/smoke.py                              # targets http://localhost:8000
    BASE_URL=https://your-app.vercel.app python scripts/smoke.py
    BASE_URL=http://localhost:8000 python scripts/smoke.py

Exit code 0 = all pass, 1 = any failure.
The server must already be running; this script does not start uvicorn.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
_failures = []

print(f"Orkestr smoke tests — target: {BASE}")
print("=" * 60)


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  [PASS] {label}")
    else:
        msg = f"  [FAIL] {label}" + (f" — {detail}" if detail else "")
        print(msg)
        _failures.append(label)


def http(method: str, path: str, body=None):
    """Return (status_code, parsed_body). body=None for GET/no-payload POST."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Ensure pristine state before starting
# ---------------------------------------------------------------------------
http("POST", "/api/dev/reseed")

# ---------------------------------------------------------------------------
section("READ — valid ORK-001")
# ---------------------------------------------------------------------------

status, body = http("GET", "/health")
check("GET /health -> {ok:true}", status == 200 and body == {"ok": True}, str(body))

status, body = http("GET", "/api/status/ORK-001")
check("GET /api/status/ORK-001 -> plan_ready",
      status == 200 and body.get("phase") == "plan_ready", str(body))

status, body = http("GET", "/api/negotiation/ORK-001")
check("GET /api/negotiation/ORK-001 -> 10 messages",
      status == 200 and isinstance(body, list) and len(body) == 10,
      f"got {len(body) if isinstance(body, list) else body}")

status, body = http("GET", "/api/plan/ORK-001")
check("GET /api/plan/ORK-001 -> per_person=80",
      status == 200 and body.get("per_person") == 80, str(body.get("per_person")))
check("GET /api/plan/ORK-001 -> venue Seoul Garden",
      status == 200 and (body.get("venue") or {}).get("name") == "Seoul Garden",
      str((body.get("venue") or {}).get("name")))

status, body = http("GET", "/api/handshake/ORK-001")
check("GET /api/handshake/ORK-001 -> status co-signed",
      status == 200 and body.get("status") == "co-signed", str(body.get("status")))
check("GET /api/handshake/ORK-001 -> merchant Seoul Garden",
      status == 200 and body.get("merchant") == "Seoul Garden", str(body.get("merchant")))

status, body = http("GET", "/api/expenses/ORK-001")
check("GET /api/expenses/ORK-001 -> 3 expenses",
      status == 200 and isinstance(body, list) and len(body) == 3,
      f"got {len(body) if isinstance(body, list) else body}")

status, body = http("GET", "/api/settlement/ORK-001")
transfers = body.get("transfers", []) if isinstance(body, dict) else []
net = body.get("net", {}) if isinstance(body, dict) else {}
check("GET /api/settlement/ORK-001 -> 3 transfers",
      status == 200 and len(transfers) == 3, f"got {len(transfers)}")
check("GET /api/settlement/ORK-001 -> sum(net)==0",
      status == 200 and sum(net.values()) == 0,
      f"sum={sum(net.values()) if net else 'n/a'}")

# ---------------------------------------------------------------------------
section("UNKNOWN-SESSION — all must return 404")
# ---------------------------------------------------------------------------

for endpoint in [
    "/api/status/NOPE",
    "/api/negotiation/NOPE",
    "/api/plan/NOPE",
    "/api/handshake/NOPE",
    "/api/expenses/NOPE",
    "/api/settlement/NOPE",
]:
    status, body = http("GET", endpoint)
    check(f"GET {endpoint} -> 404",
          status == 404, f"got {status} body={body}")

# ---------------------------------------------------------------------------
section("VALID-EMPTY-EXPENSES — no compute_plan side effect")
# ---------------------------------------------------------------------------

status, body = http("POST", "/api/session/start", {})
scratch = (body or {}).get("session_id", "")
check("POST /api/session/start -> session_id",
      status == 200 and bool(scratch), str(body))
if scratch:
    status, body = http("GET", f"/api/expenses/{scratch}")
    check(f"GET /api/expenses/{{scratch}} -> [] (200)",
          status == 200 and body == [], f"got status={status} body={body}")

# ---------------------------------------------------------------------------
section("CONSTRAINTS FAILURE BATTERY")
# ---------------------------------------------------------------------------

status, body = http("POST", "/api/constraints", {})
check("POST /api/constraints {} -> 400 (session_id required)",
      status == 400, f"got {status}")

status, body = http("POST", "/api/constraints", {"session_id": "NOPE", "id": "P-002"})
check("POST /api/constraints {session_id:NOPE} -> 404",
      status == 404, f"got {status}")

status, body = http("POST", "/api/constraints", {"session_id": "ORK-001"})
check("POST /api/constraints {session_id:ORK-001, no id} -> 400 (id required)",
      status == 400, f"got {status}")

# ---------------------------------------------------------------------------
section("APPROVE FLOW with unknown-member guard")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")

status, body = http("POST", "/api/approve/ORK-001", {"person_id": "P-999"})
check("POST /api/approve/ORK-001 {P-999} -> 400 (unknown member)",
      status == 400, f"got {status} body={body}")

status, body = http("GET", "/api/status/ORK-001")
check("GET /api/status/ORK-001 still plan_ready after rejected approve",
      status == 200 and body.get("phase") == "plan_ready",
      f"got phase={body.get('phase') if body else body}")

status, body = http("POST", "/api/approve/ORK-001", {"person_id": "P-002"})
check("POST /api/approve/ORK-001 {P-002} -> 200",
      status == 200, f"got {status}")

status, body = http("GET", "/api/status/ORK-001")
check("GET /api/status/ORK-001 -> confirmed after P-002 approves",
      status == 200 and body.get("phase") == "confirmed",
      f"got phase={body.get('phase') if body else body}")

# ---------------------------------------------------------------------------
section("SETTLE VALIDATION BATTERY — all must 4xx, settlement must NOT mutate")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")

_, settlement_before = http("GET", "/api/settlement/ORK-001")

status, body = http("POST", "/api/settle/ORK-001", {})
check("POST /api/settle/ORK-001 {} -> 400",
      status == 400, f"got {status}")

status, body = http("POST", "/api/settle/ORK-001", {"person_id": "P-999"})
check("POST /api/settle/ORK-001 {person_id:P-999} -> 400",
      status == 400, f"got {status}")

status, body = http("POST", "/api/settle/ORK-001", {"fronted": "nope"})
check('POST /api/settle/ORK-001 {fronted:"nope"} -> 400',
      status == 400, f"got {status}")

status, body = http("POST", "/api/settle/ORK-001", {"fronted": {"P-999": 50}})
check("POST /api/settle/ORK-001 {fronted:{P-999:50}} -> 400",
      status == 400, f"got {status}")

status, body = http("POST", "/api/settle/ORK-001", {"fronted": {"P-001": -5}})
check("POST /api/settle/ORK-001 {fronted:{P-001:-5}} -> 400",
      status == 400, f"got {status}")

status, body = http("POST", "/api/settle/NOPE", {"person_id": "P-002"})
check("POST /api/settle/NOPE -> 404",
      status == 404, f"got {status}")

_, settlement_after = http("GET", "/api/settlement/ORK-001")
check("Settlement unchanged after validation battery",
      settlement_before == settlement_after,
      "settlement mutated during validation battery")

# ---------------------------------------------------------------------------
section("SETTLE IDEMPOTENCY")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")

status, body = http("POST", "/api/settle/ORK-001", {"person_id": "P-004"})
check("POST /api/settle/ORK-001 {P-004} -> 200",
      status == 200, f"got {status}")

status, body = http("GET", "/api/settlement/ORK-001")
transfers = (body or {}).get("transfers", [])
p004_transfers = [t for t in transfers if t.get("from") == "P-004"]
check("P-004 transfer status=settled after settle",
      p004_transfers and p004_transfers[0].get("status") == "settled",
      str(p004_transfers))
first_hash = p004_transfers[0].get("tx_hash") if p004_transfers else None
check("P-004 tx_hash is non-null after settle",
      bool(first_hash), f"got {first_hash}")

status, body = http("POST", "/api/settle/ORK-001", {"person_id": "P-004"})
check("POST /api/settle/ORK-001 {P-004} again -> 200 (idempotent)",
      status == 200, f"got {status}")

status, body = http("GET", "/api/settlement/ORK-001")
transfers = (body or {}).get("transfers", [])
p004_transfers = [t for t in transfers if t.get("from") == "P-004"]
second_hash = p004_transfers[0].get("tx_hash") if p004_transfers else None
check("P-004 tx_hash unchanged after second settle",
      first_hash is not None and first_hash == second_hash,
      f"first={first_hash} second={second_hash}")

# ---------------------------------------------------------------------------
section("OTHER FAIL BATTERY")
# ---------------------------------------------------------------------------

status, body = http("POST", "/api/approve/ORK-001", {})
check("POST /api/approve/ORK-001 {} -> 400 (person_id required)",
      status == 400, f"got {status}")

status, body = http("POST", "/api/expense/ORK-001", {"paid_by": "P-999", "amount": 50})
check("POST /api/expense/ORK-001 {paid_by:P-999} -> 400 (not a member)",
      status == 400, f"got {status}")

status, body = http("POST", "/api/expense/ORK-001", {"paid_by": "P-001", "amount": "lots"})
check('POST /api/expense/ORK-001 {amount:"lots"} -> 400 (not numeric)',
      status == 400, f"got {status}")

# ---------------------------------------------------------------------------
section("RESET + RE-PROVE")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")
status, body = http("GET", "/api/settlement/ORK-001")
transfers = (body or {}).get("transfers", [])
net = (body or {}).get("net", {})
check("After reseed: 3 transfers",
      status == 200 and len(transfers) == 3, f"got {len(transfers)}")
check("After reseed: all transfers pending",
      all(t.get("status") == "pending" for t in transfers),
      str([(t.get("from"), t.get("status")) for t in transfers]))
check("After reseed: all tx_hash null",
      all(t.get("tx_hash") is None for t in transfers),
      str([(t.get("from"), t.get("tx_hash")) for t in transfers]))
check("After reseed: sum(net)==0",
      sum(net.values()) == 0, f"sum={sum(net.values()) if net else 'n/a'}")
check("After reseed: negotiation still 10 messages",
      *((lambda st, b: (st == 200 and isinstance(b, list) and len(b) == 10,
                        f"got {len(b) if isinstance(b, list) else b}")
         )(*http("GET", "/api/negotiation/ORK-001"))))
check("After reseed: plan per_person=80",
      *((lambda st, b: (st == 200 and b.get("per_person") == 80,
                        str(b.get("per_person")))
         )(*http("GET", "/api/plan/ORK-001"))))

# ---------------------------------------------------------------------------
# Final reseed so ORK-001 ends pristine
# ---------------------------------------------------------------------------
http("POST", "/api/dev/reseed")

# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
if _failures:
    print(f"  RESULT: {len(_failures)} FAILURE(S)")
    for f in _failures:
        print(f"    - {f}")
    print(f"{'='*60}")
    sys.exit(1)
else:
    total = sum(1 for line in open(__file__) if "check(" in line)
    print(f"  RESULT: ALL PASS")
    print(f"{'='*60}")
    sys.exit(0)
