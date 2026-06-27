"""Exa integration smoke tests for Orkestr.

Stdlib only (urllib.request, json, os, sys). No pytest, no third-party deps.
Reads BASE_URL from env (default: http://localhost:8000).
Reads USE_EXA / EXA_API_KEY from env (loaded via dotenv in agents.discovery).

Usage:
    python scripts/exa_smoke.py                          # all safe-mode checks
    USE_EXA=true python scripts/exa_smoke.py             # + fake-key check
    USE_EXA=true EXA_API_KEY=... python scripts/exa_smoke.py  # + live query

Exit code 0 = all required checks pass.
Exit code 1 = at least one required check failed.
"""
import json
import os
import sys
import urllib.error
import urllib.request

# Ensure repo root is on sys.path when running as `python scripts/exa_smoke.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
_failures: list = []
_passes: int = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global _passes
    if ok:
        print(f"  [PASS] {label}")
        _passes += 1
    else:
        msg = f"  [FAIL] {label}" + (f" — {detail}" if detail else "")
        print(msg)
        _failures.append(label)


def http(method: str, path: str, body=None, env_override: dict = None):
    """Return (status_code, parsed_body). env_override not used for HTTP — for doc only."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
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


print(f"Orkestr Exa smoke tests — target: {BASE}")
print("=" * 60)

# ---------------------------------------------------------------------------
section("STATIC IMPORT CHECKS (no server needed)")
# ---------------------------------------------------------------------------

import_ok = True
try:
    import agents.discovery as D
    print("  [PASS] import agents.discovery")
    _passes += 1
except Exception as e:
    print(f"  [FAIL] import agents.discovery — {e}")
    _failures.append("import agents.discovery")
    import_ok = False

try:
    import api.main  # noqa: F401
    print("  [PASS] import api.main")
    _passes += 1
except Exception as e:
    print(f"  [FAIL] import api.main — {e}")
    _failures.append("import api.main")

if import_ok:
    section("ENV PRESENCE REPORT (no secret values)")
    report = D.get_env_presence_report()
    for k, v in report.items():
        print(f"  {k}: {v}")

    # Confirm no secret values are in the report
    secret_keys = ["EXA_API_KEY", "OPENAI_API_KEY", "STRIPE_SECRET_KEY"]
    for sk in secret_keys:
        val = report.get(sk, "")
        check(
            f"get_env_presence_report {sk} is yes/no only",
            val in ("yes", "no"),
            f"got: {val!r}",
        )

    section("UNIT: discover_venues disabled mode (USE_EXA=false)")
    old_use_exa = os.environ.pop("USE_EXA", None)
    os.environ["USE_EXA"] = "false"
    result = D.discover_venues(query="Singapore Korean BBQ dinner", limit=3)
    check("ok=true when disabled", result.get("ok") is True, str(result.get("ok")))
    check("enabled=false when disabled", result.get("enabled") is False, str(result.get("enabled")))
    check("source=disabled", result.get("source") == "disabled", result.get("source"))
    check("venues=[] when disabled", result.get("venues") == [], str(result.get("venues")))
    check("no 500 when disabled", "traceback" not in str(result).lower(), "traceback found")
    if old_use_exa is not None:
        os.environ["USE_EXA"] = old_use_exa
    else:
        os.environ.pop("USE_EXA", None)

    section("UNIT: discover_venues missing-key mode (USE_EXA=true, no EXA_API_KEY)")
    old_key = os.environ.pop("EXA_API_KEY", None)
    old_use_exa2 = os.environ.get("USE_EXA")
    os.environ["USE_EXA"] = "true"
    result2 = D.discover_venues(query="Singapore halal dinner", limit=3)
    check("ok=true with missing key", result2.get("ok") is True, str(result2.get("ok")))
    check("source=missing_key", result2.get("source") == "missing_key", result2.get("source"))
    check("venues=[] with missing key", result2.get("venues") == [], str(result2.get("venues")))
    check("no traceback in response", "traceback" not in str(result2).lower(), "traceback found")
    check("no secret in reason field", not any(
        (len(v) > 20 and v.replace("-", "").replace("_", "").isalnum())
        for v in [str(result2.get("reason", ""))]
    ), "potential secret in reason")
    if old_key is not None:
        os.environ["EXA_API_KEY"] = old_key
    if old_use_exa2 is not None:
        os.environ["USE_EXA"] = old_use_exa2
    else:
        os.environ.pop("USE_EXA", None)

    section("UNIT: query builder")
    q = D.build_venue_query(query="Korean BBQ near VivoCity")
    check("query builder with explicit query", "singapore" in q.lower(), f"got: {q!r}")
    q2 = D.build_venue_query(constraints={"dietary": ["halal", "vegetarian"], "budget_max": 60})
    check("query builder with constraints has halal", "halal" in q2.lower(), f"got: {q2!r}")
    check("query builder has Singapore", "singapore" in q2.lower(), f"got: {q2!r}")
    print(f"  sample query: {q2!r}")

# ---------------------------------------------------------------------------
section("HTTP: Exa endpoint — basic shape (server state-aware)")
# ---------------------------------------------------------------------------

status, body = http("POST", "/api/discovery/venues",
                    {"query": "Singapore halal Korean BBQ", "limit": 3})
check("POST /api/discovery/venues HTTP 200", status == 200, f"got {status}")
check("ok=true", (body or {}).get("ok") is True, str((body or {}).get("ok")))
check("enabled is bool", isinstance((body or {}).get("enabled"), bool), str(type((body or {}).get("enabled"))))
_valid_sources = ("exa", "missing_key", "error", "disabled")
check("source is valid", (body or {}).get("source") in _valid_sources, (body or {}).get("source"))
check("venues key present", "venues" in (body or {}), str(list((body or {}).keys())))
_server_exa_enabled = (body or {}).get("enabled") is True
print(f"  (server USE_EXA enabled: {_server_exa_enabled}, source: {(body or {}).get('source')})")

# ---------------------------------------------------------------------------
section("HTTP: Exa endpoint — malformed request -> 400")
# ---------------------------------------------------------------------------

status, body = http("POST", "/api/discovery/venues", {"query": "test", "limit": -1})
check("limit=-1 -> 400", status == 400, f"got {status}")

status, body = http("POST", "/api/discovery/venues", {"query": "test", "limit": "many"})
check('limit="many" -> 400', status == 400, f"got {status}")

status, body = http("POST", "/api/discovery/venues", {"query": "test", "limit": 0})
check("limit=0 -> 400", status == 400, f"got {status}")

# Empty body should not 500 (builds a generic query)
status, body = http("POST", "/api/discovery/venues", {})
check("empty body -> 200 (generic query built)", status == 200, f"got {status}")

# ---------------------------------------------------------------------------
section("HTTP: ORK-001 frozen values — unchanged by Exa flags")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")

status, body = http("GET", "/api/status/ORK-001")
check("ORK-001 status=plan_ready", status == 200 and (body or {}).get("phase") == "plan_ready",
      str((body or {}).get("phase")))

status, body = http("GET", "/api/negotiation/ORK-001")
check("ORK-001 negotiation=10 messages",
      status == 200 and isinstance(body, list) and len(body) == 10,
      f"got {len(body) if isinstance(body, list) else body}")

status, body = http("GET", "/api/plan/ORK-001")
check("ORK-001 plan per_person=80",
      status == 200 and (body or {}).get("per_person") == 80,
      str((body or {}).get("per_person")))
check("ORK-001 plan venue=Seoul Garden",
      status == 200 and ((body or {}).get("venue") or {}).get("name") == "Seoul Garden",
      str(((body or {}).get("venue") or {}).get("name")))

status, body = http("GET", "/api/handshake/ORK-001")
check("ORK-001 handshake status=co-signed",
      status == 200 and (body or {}).get("status") == "co-signed",
      str((body or {}).get("status")))

status, body = http("GET", "/api/settlement/ORK-001")
transfers = (body or {}).get("transfers", [])
net = (body or {}).get("net", {})
check("ORK-001 settlement=3 transfers",
      status == 200 and len(transfers) == 3, f"got {len(transfers)}")
check("ORK-001 net sum=0",
      status == 200 and sum(net.values()) == 0,
      f"sum={sum(net.values()) if net else 'n/a'}")

# ---------------------------------------------------------------------------
# Live Exa test — only if EXA_API_KEY is present AND USE_EXA=true
# ---------------------------------------------------------------------------

from dotenv import load_dotenv as _dotenv_load
_dotenv_load()
_exa_key_present = bool(os.environ.get("EXA_API_KEY", "").strip())
_use_exa_env = os.environ.get("USE_EXA", "").lower()
_exa_flag_on = _use_exa_env in ("true", "1", "yes")

if _exa_key_present and _exa_flag_on:
    section("LIVE EXA TEST (EXA_API_KEY present, USE_EXA=true)")
    print("  Note: API key is present but will NOT be printed.")

    status, body = http("POST", "/api/discovery/venues", {
        "query": "Singapore group dinner near VivoCity, halal friendly, vegetarian options, budget 30 to 50 SGD per person",
        "limit": 5,
    })
    check("live query HTTP 200", status == 200, f"got {status}")

    if status == 200 and body:
        check("live ok=true", body.get("ok") is True, str(body.get("ok")))
        venues = body.get("venues", [])
        check("live venues is a list", isinstance(venues, list), type(venues).__name__)
        check("live no crash (source != error always)", body.get("source") in ("exa", "missing_key", "error", "disabled"), body.get("source"))

        if venues:
            print(f"  Discovered {len(venues)} venue(s):")
            req_keys = {"id", "name", "halal", "vegetarian", "price_per_head",
                        "capacity", "opens", "closes", "near_arcade"}
            for i, v in enumerate(venues, 1):
                name = v.get("name", "?")
                url = v.get("source_url", "no url")
                conf = v.get("confidence", "?")
                evidence_count = len(v.get("source_highlights", []))
                print(f"  [{i}] {name!r} | confidence={conf} | highlights={evidence_count} | url={url[:60]}")
                missing_keys = req_keys - set(v.keys())
                check(f"venue [{i}] has required keys", not missing_keys,
                      f"missing: {missing_keys}")
                # confirm no API key leaks in venue response
                venue_str = json.dumps(v)
                key_val = os.environ.get("EXA_API_KEY", "NOTPRESENT")
                check(f"venue [{i}] does not contain API key",
                      key_val == "NOTPRESENT" or key_val not in venue_str,
                      "key found in response!")
        else:
            print("  Exa returned 0 venues (possible rate limit or no matches). Not a failure.")
            check("live source documented", body.get("source") in ("exa", "error"), body.get("source"))
else:
    section("LIVE EXA TEST — SKIPPED")
    if not _exa_key_present:
        print("  EXA_API_KEY not visible to Python. Skipping live test.")
    elif not _exa_flag_on:
        print("  USE_EXA not set to true. Skipping live test.")
    print("  All safe-mode checks above still required.")

# ---------------------------------------------------------------------------
section("FINAL RESET")
# ---------------------------------------------------------------------------

http("POST", "/api/dev/reseed")
status, body = http("GET", "/api/plan/ORK-001")
check("ORK-001 pristine after final reseed (per_person=80)",
      status == 200 and (body or {}).get("per_person") == 80,
      str((body or {}).get("per_person")))

# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
if _failures:
    print(f"  RESULT: {len(_failures)} FAILURE(S) / {_passes + len(_failures)} checks")
    for f in _failures:
        print(f"    - {f}")
    print(f"{'='*60}")
    sys.exit(1)
else:
    print(f"  RESULT: ALL {_passes} CHECKS PASS")
    print(f"{'='*60}")
    sys.exit(0)
