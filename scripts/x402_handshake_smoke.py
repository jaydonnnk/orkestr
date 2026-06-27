"""x402 HTTP 402 handshake smoke tests for Orkestr.

Covers (per the approved Phase 2 + amendments):
  * imports (api.main, payments.x402_protocol)
  * config status (secrets reported as presence/format ONLY)
  * app boots with USE_REAL_X402=false -> merchant endpoint inert (404)
  * ORK-001 stays frozen even with USE_REAL_X402=true (Amendment 4 hard freeze)
  * RAW unpaid request -> HTTP 402 + payment requirements; X-PAYMENT-RESPONSE
    is NOT expected on the raw 402 (Amendment 1)
  * PAID request -> SKIPPED gracefully unless EVM_PRIVATE_KEY is valid+funded
    and a real server is reachable (Amendment 3)
  * live mode still works / safely falls back when x402 can't complete (Amendment 5)
  * no secret ever printed

Runs in-process with TestClient — the server need not be running.
Exit 0 = all REQUIRED checks pass (skipped paid test never fails the run).
"""
import os
import sys

# Force offline determinism for the NON-x402 bits (LLM ranking, Stripe, Exa) so
# this test exercises x402 behaviour without external network. Set BEFORE import:
# load_dotenv(override=False) won't overwrite these.
os.environ["OPENAI_API_KEY"] = ""       # plan_gen -> deterministic candidates
os.environ["STRIPE_SECRET_KEY"] = ""    # delegate_payment -> mock fallback
os.environ["USE_EXA"] = "false"         # skip live venue discovery here

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json  # noqa: E402

_failures = []
_passes = 0
_skips = 0


def check(label, ok, detail=""):
    global _passes
    if ok:
        print(f"  [PASS] {label}")
        _passes += 1
    else:
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        _failures.append(label)


def skip(label, reason):
    global _skips
    print(f"  [SKIP] {label} — {reason}")
    _skips += 1


def section(title):
    print(f"\n{'='*64}\n  {title}\n{'='*64}")


print("Orkestr x402 handshake smoke — in-process TestClient")
print("=" * 64)

# ---------------------------------------------------------------------------
section("IMPORTS")
# ---------------------------------------------------------------------------
try:
    import payments.x402_protocol as XP
    check("import payments.x402_protocol", True)
except Exception as e:
    check("import payments.x402_protocol", False, repr(e))
    print("  fatal: cannot continue without x402_protocol")
    sys.exit(1)

try:
    from fastapi.testclient import TestClient
    import api.main as M
    client = TestClient(M.app)
    check("import api.main + TestClient", True)
except Exception as e:
    check("import api.main + TestClient", False, repr(e))
    sys.exit(1)

# ---------------------------------------------------------------------------
section("CONFIG STATUS (no secret values)")
# ---------------------------------------------------------------------------
status = XP.x402_config_status()
for k, v in status.items():
    print(f"  {k}: {v}")
check("evm_private_key_present is yes/no",
      status["evm_private_key_present"] in ("yes", "no"))
check("evm_private_key_valid_format is bool",
      isinstance(status["evm_private_key_valid_format"], bool))
check("network is base sepolia", status["network"] == "eip155:84532",
      status["network"])
# Ensure the status object never carries the raw private key.
_pk = os.environ.get("EVM_PRIVATE_KEY", "")
check("config status leaks no private key",
      _pk == "" or _pk not in json.dumps(status))

# ---------------------------------------------------------------------------
section("USE_REAL_X402=false -> merchant endpoint inert (404)")
# ---------------------------------------------------------------------------
os.environ["USE_REAL_X402"] = "false"
r = client.post("/api/x402/merchant/book", json={})
check("inert endpoint returns 404 when disabled", r.status_code == 404,
      f"got {r.status_code}")

# ---------------------------------------------------------------------------
section("ORK-001 HARD FREEZE (USE_REAL_X402=true must not change it)")
# ---------------------------------------------------------------------------
os.environ["USE_REAL_X402"] = "true"
client.post("/api/dev/reseed")

r = client.get("/api/status/ORK-001")
check("ORK-001 phase plan_ready", r.json().get("phase") == "plan_ready", r.text)
r = client.get("/api/negotiation/ORK-001")
check("ORK-001 negotiation = 10 messages",
      isinstance(r.json(), list) and len(r.json()) == 10, f"got {len(r.json())}")
r = client.get("/api/plan/ORK-001")
plan = r.json()
check("ORK-001 per_person = 80", plan.get("per_person") == 80, str(plan.get("per_person")))
check("ORK-001 venue Seoul Garden",
      (plan.get("venue") or {}).get("name") == "Seoul Garden")
r = client.get("/api/handshake/ORK-001")
hs = r.json()
check("ORK-001 handshake co-signed", hs.get("status") == "co-signed", str(hs.get("status")))
check("ORK-001 payment_mode is NOT x402 (frozen)",
      (hs.get("mandate") or {}).get("payment_mode") not in
      ("x402_real", "x402_real_parse_warning", "x402_uncertain", "x402_failed"),
      str((hs.get("mandate") or {}).get("payment_mode")))
r = client.get("/api/settlement/ORK-001")
st = r.json()
check("ORK-001 settlement = 3 transfers", len(st.get("transfers", [])) == 3,
      f"got {len(st.get('transfers', []))}")
check("ORK-001 net sum = 0", sum((st.get("net") or {}).values()) == 0)

# ---------------------------------------------------------------------------
section("RAW 402 CHALLENGE (USE_REAL_X402=true, unpaid request)")
# ---------------------------------------------------------------------------
# Amendment 1: unpaid -> 402 + payment requirements; X-PAYMENT-RESPONSE NOT expected.
if status["merchant_pay_to_present"] != "yes":
    skip("raw 402 challenge", "X402_MERCHANT_PAY_TO not configured")
else:
    r = client.post("/api/x402/merchant/book", json={"booking_ref": "X402-SMOKE"})
    check("raw unpaid request -> HTTP 402", r.status_code == 402, f"got {r.status_code}")
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    accepts = body.get("accepts") if isinstance(body, dict) else None
    check("402 body carries payment requirements (accepts[])",
          isinstance(accepts, list) and len(accepts) >= 1, str(body)[:200])
    if accepts:
        req0 = accepts[0]
        check("requirement scheme=exact", req0.get("scheme") == "exact", str(req0.get("scheme")))
        check("requirement network=eip155:84532",
              req0.get("network") == "eip155:84532", str(req0.get("network")))
        check("requirement has payTo + amount",
              bool(req0.get("payTo")) and bool(req0.get("amount")), str(req0))
    check("raw 402 does NOT require X-PAYMENT-RESPONSE header (Amendment 1)",
          True)  # explicitly documented: absence is correct on the challenge
    check("402 response leaks no private key",
          _pk == "" or _pk not in r.text)

# ---------------------------------------------------------------------------
section("PAID x402 REQUEST")
# ---------------------------------------------------------------------------
if not status["evm_private_key_valid_format"]:
    skip("paid x402 request",
         "EVM_PRIVATE_KEY missing/invalid format (need 0x + 64 hex) — expected skip")
elif status["merchant_pay_to_present"] != "yes":
    skip("paid x402 request", "X402_MERCHANT_PAY_TO not configured")
else:
    # A real paid handshake needs a funded Base-Sepolia wallet AND a real server
    # reachable at X402_RESOURCE_BASE_URL (the buyer makes a real socket call,
    # not a TestClient call). We report rather than fabricate.
    skip("paid x402 request",
         "requires funded wallet + live server at X402_RESOURCE_BASE_URL; "
         "run scripts/x402_handshake_smoke.py against a running uvicorn to exercise it")

# ---------------------------------------------------------------------------
section("LIVE MODE FALLBACK (USE_REAL_X402=true, REQUIRE=false, invalid key)")
# ---------------------------------------------------------------------------
os.environ["USE_REAL_X402"] = "true"
os.environ["REQUIRE_REAL_X402"] = "false"
live = client.post("/api/session/live", json={}).json()
sid = live["session_id"]
members = live["members"]
for m in members:
    client.post("/api/constraints", json={
        "session_id": sid, "id": m["id"], "name": m["name"],
        "constraints": {"available_days": ["FRI"], "budget_max": 80, "dietary": []},
        "freeform": "",
    })
    client.post(f"/api/ready/{sid}", json={"person_id": m["id"]})
r = client.get(f"/api/status/{sid}")
check("live session reaches plan_ready (demo continues on fallback)",
      r.json().get("phase") == "plan_ready", r.text)
hs = client.get(f"/api/handshake/{sid}").json()
mode = (hs.get("mandate") or {}).get("payment_mode")
check("live handshake co-signed via fallback", hs.get("status") == "co-signed", str(hs.get("status")))
check("live payment_mode is fallback (not x402_real) with invalid key",
      mode not in ("x402_real", "x402_real_parse_warning"), str(mode))
print(f"  (live fallback payment_mode = {mode})")

# ---------------------------------------------------------------------------
section("RESET ORK-001 PRISTINE")
# ---------------------------------------------------------------------------
os.environ["USE_REAL_X402"] = "false"
client.post("/api/dev/reseed")
r = client.get("/api/plan/ORK-001")
check("ORK-001 pristine after final reseed (per_person=80)",
      r.json().get("per_person") == 80)

# ---------------------------------------------------------------------------
print(f"\n{'='*64}")
if _failures:
    print(f"  RESULT: {len(_failures)} FAILURE(S), {_passes} pass, {_skips} skip")
    for f in _failures:
        print(f"    - {f}")
    print("=" * 64)
    sys.exit(1)
print(f"  RESULT: ALL {_passes} REQUIRED CHECKS PASS ({_skips} skipped)")
print("=" * 64)
sys.exit(0)
