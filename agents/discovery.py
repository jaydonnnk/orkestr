"""Exa venue discovery module for Orkestr.

Discovers real venues from the web using the Exa search API and converts
results into the standard venue shape used by agents/convener.py.

All feature flags default to OFF — existing MVP is unaffected.
Never mutates sessions. Never affects ORK-001.
Never crashes the app on any Exa failure.

Env flags:
    USE_EXA                       — master on/off (default: false)
    USE_EXA_IN_PLANNING           — allow Exa venues into non-ORK planning (default: false)
    USE_OPENAI_FOR_EXA_EXTRACTION — optional OpenAI extraction enhancement (default: false)
    EXA_API_KEY                   — required for live Exa; missing → safe disabled
    EXA_MAX_RESULTS               — cap for num_results (default: 10)
    EXA_CACHE_TTL_SECONDS         — cache TTL in seconds (default: 900 = 15 min)
    OPENAI_API_KEY                — only used if USE_OPENAI_FOR_EXA_EXTRACTION=true
    OPENAI_MODEL                  — model for extraction (default: gpt-4o-mini)
"""

import hashlib
import json
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------

_DEFAULT_TTL = 900          # 15 minutes
_DEFAULT_PRICE_PER_HEAD = 50
_DEFAULT_CAPACITY = 6
_DEFAULT_OPENS = "11:00"
_DEFAULT_CLOSES = "22:00"
_EXA_MAX_RESULTS_HARD_CAP = 10

_CACHE: dict = {}


# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------

def _flag_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("true", "1", "yes")


def is_exa_enabled() -> bool:
    return _flag_bool("USE_EXA")


def is_exa_planning_enabled() -> bool:
    return _flag_bool("USE_EXA_IN_PLANNING")


def is_openai_extraction_enabled() -> bool:
    return _flag_bool("USE_OPENAI_FOR_EXA_EXTRACTION")


def get_env_presence_report() -> dict:
    """Returns yes/no presence only — never exposes secret values."""
    secret_keys = ["EXA_API_KEY", "OPENAI_API_KEY", "STRIPE_SECRET_KEY"]
    flag_keys = ["USE_EXA", "USE_EXA_IN_PLANNING", "USE_OPENAI_FOR_EXA_EXTRACTION",
                 "EXA_MAX_RESULTS", "EXA_CACHE_TTL_SECONDS"]
    report = {}
    for k in secret_keys:
        report[k] = "yes" if os.environ.get(k, "").strip() else "no"
    for k in flag_keys:
        v = os.environ.get(k)
        report[k] = v if v is not None else "unset"
    return report


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_ttl() -> int:
    try:
        return max(0, int(os.environ.get("EXA_CACHE_TTL_SECONDS", str(_DEFAULT_TTL))))
    except (ValueError, TypeError):
        return _DEFAULT_TTL


def _cache_key(query: str, limit: int, constraints=None) -> str:
    parts = {
        "q": query.strip().lower(),
        "l": limit,
        "c": constraints if constraints else None,
        "oai": is_openai_extraction_enabled(),
    }
    return hashlib.md5(
        json.dumps(parts, sort_keys=True, default=str).encode()
    ).hexdigest()


def _cache_get(key: str):
    entry = _CACHE.get(key)
    if entry and time.time() < entry.get("expires", 0):
        return entry.get("result")
    _CACHE.pop(key, None)
    return None


def _cache_set(key: str, value) -> None:
    try:
        _CACHE[key] = {"result": value, "expires": time.time() + _cache_ttl()}
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------

def build_venue_query(
    personas=None,
    constraints=None,
    location: str = None,
    query: str = None,
) -> str:
    """Build a human-readable Exa query from group constraints and preferences."""
    if query and isinstance(query, str) and query.strip():
        base = query.strip()
        if personas and isinstance(personas, list):
            party_size = len(personas)
            has_size = (
                f"{party_size} people" in base
                or f"{party_size} person" in base
                or f"{party_size} pax" in base
            )
            if not has_size:
                base = f"{base} for {party_size} people"
        if "singapore" not in base.lower():
            base = f"Singapore {base}"
        return base

    parts = ["Singapore group dinner venue"]

    dietary_terms: set = set()
    budgets: list = []
    cuisine_terms: set = set()
    location_terms: set = set()

    has_vegetarian = False
    has_meat_eater = False

    if personas and isinstance(personas, list):
        party_size = len(personas)
        parts.append(f"for {party_size} people")

        for p in personas:
            c = p.get("constraints") or {}
            diet = [str(d).lower() for d in (c.get("dietary") or [])]
            is_veg = any(d in ("vegetarian", "vegan") for d in diet)
            has_vegetarian = has_vegetarian or is_veg
            # Anyone without a veg restriction (or who explicitly wants meat) is an
            # omnivore the venue must also serve.
            if not is_veg:
                has_meat_eater = True
            if "meat" in str(p.get("freeform", "")).lower():
                has_meat_eater = True

            for d in diet:
                if d == "halal":
                    dietary_terms.add("halal-friendly")
                elif d == "vegetarian":
                    dietary_terms.add("vegetarian options")
                elif d == "vegan":
                    dietary_terms.add("vegan-friendly")
                elif d == "no_raw_fish":
                    dietary_terms.add("no raw fish")

            bmax = c.get("budget_max")
            if isinstance(bmax, (int, float)) and bmax > 0:
                budgets.append(bmax)

            for cu in c.get("cuisine") or []:
                cuisine_terms.add(str(cu).lower())

            for loc_key in ("location", "area", "near"):
                loc = c.get(loc_key)
                if loc:
                    location_terms.add(str(loc))

    elif constraints and isinstance(constraints, dict):
        loc = constraints.get("location") or location
        if loc:
            location_terms.add(str(loc))
        for d in constraints.get("dietary") or []:
            dietary_terms.add(str(d))
        bmax = constraints.get("budget_max")
        if isinstance(bmax, (int, float)) and bmax > 0:
            budgets.append(bmax)

    if location and location not in location_terms:
        location_terms.add(location)

    if location_terms:
        parts.append(f"near {', '.join(sorted(location_terms))}")

    # Mixed group: a vegetarian AND a meat-eater. Asking for "vegetarian options"
    # alone pulls veg-only restaurants that fail the meat-eaters, so request a
    # venue that serves both rather than a vegetarian-only place.
    if has_vegetarian and has_meat_eater:
        dietary_terms.discard("vegetarian options")
        dietary_terms.discard("vegan-friendly")
        dietary_terms.add("serving meat dishes and vegetarian options")

    if dietary_terms:
        parts.extend(sorted(dietary_terms))

    if cuisine_terms:
        parts.append(f"{', '.join(sorted(cuisine_terms))} cuisine")

    if budgets:
        b_min = min(budgets)
        b_max = max(budgets)
        if b_min == b_max:
            parts.append(f"budget around {b_min} SGD per person")
        else:
            parts.append(f"budget {b_min} to {b_max} SGD per person")

    parts.append("restaurant group dining booking")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _safe_get(obj, key, default=None):
    """Access obj[key] or obj.key safely, for both dict and object results."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _full_text(title: str, highlights_text: str) -> str:
    return f"{title} {highlights_text}".lower()


def _infer_halal(title: str, highlights_text: str) -> bool:
    return "halal" in _full_text(title, highlights_text)


def _infer_vegetarian(title: str, highlights_text: str) -> bool:
    text = _full_text(title, highlights_text)
    return any(w in text for w in ("vegetarian", "vegan", "plant-based", "meat-free"))


_NON_RESTAURANT_TERMS = (
    "venue rental", "event space", "event venue", "events rental", "function room",
    "wedding", "conference", "co-working", "coworking", "office space",
    "party hall", "banquet hall rental", "caterer", "catering service",
    "real estate", "for rent", "for lease", "hotel booking", "airbnb",
    "things to do", "best restaurants", "top 10", "guide to", "listicle",
)


def _looks_like_restaurant(title: str) -> bool:
    """Heuristic: keep dining venues, drop rentals/event-spaces/listicles.

    Conservative — only rejects on an explicit non-dining signal so a plain
    restaurant name (which carries no positive keyword) still passes.
    """
    t = title.lower()
    return not any(term in t for term in _NON_RESTAURANT_TERMS)


def _infer_near_arcade(title: str, highlights_text: str) -> bool:
    text = _full_text(title, highlights_text)
    return any(w in text for w in (
        "arcade", "timezone", "entertainment", "activity", "bowling",
        "laser tag", "escape room", "games",
    ))


def _infer_price_per_head(highlights_text: str):
    """Extract SGD price per person from highlights text. Returns None if not found."""
    text = highlights_text.lower()
    patterns = [
        r"\$\s*(\d+(?:\.\d+)?)\s*(?:per\s*(?:head|person|pax)|\/\s*(?:head|person|pax))",
        r"sgd\s*(\d+(?:\.\d+)?)\s*(?:per\s*(?:head|person|pax)|\/\s*(?:head|person|pax))",
        r"(\d+(?:\.\d+)?)\s*sgd\s*(?:per\s*(?:head|person|pax)|\/\s*(?:head|person|pax))",
        r"(?:average|around|about|approx)[^\d]*\$\s*(\d+(?:\.\d+)?)",
        r"price\s*(?:from|around|about)?\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:sgd|per)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                val = float(m.group(1))
                if 5 <= val <= 500:
                    return val
            except (ValueError, TypeError):
                pass
    return None


def _slug_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"exa_{slug[:32]}"


def _looks_like_listicle(url: str) -> bool:
    url_lower = url.lower()
    return any(sig in url_lower for sig in (
        "/best-", "/top-", "/list-", "/guide-", "/roundup",
        "thehoneycombers", "timeout.com", "tripadvisor.com",
        "hungrygowhere", "burpple.com/guide", "zomato.com/collection",
        "yelp.com/search", "chope.co/blog", "sethlui.com",
        "ladyironchef.com", "danielfooddiary.com",
    ))


def _looks_like_official(url: str) -> bool:
    url_lower = url.lower()
    return any(sig in url_lower for sig in (
        ".com.sg", "/reservation", "/menu", "/booking",
        "openrice.com", "chope.co/restaurants",
    ))


def _confidence_score(
    title: str, url: str, highlights_text: str, query: str
) -> tuple:
    score = 0.30
    reasons = []

    if highlights_text.strip():
        score += 0.10
        reasons.append("highlights present")

    query_terms = [t.lower() for t in re.split(r"\W+", query) if len(t) > 3]
    full = _full_text(title, highlights_text)
    hits = sum(1 for t in query_terms if t in full)
    if hits > 0:
        bonus = min(0.25, hits * 0.07)
        score += bonus
        reasons.append(f"{hits} query term(s) matched in content")

    if _looks_like_official(url):
        score += 0.20
        reasons.append("official venue URL pattern")

    if "singapore" in full:
        score += 0.08
        reasons.append("Singapore mentioned in content")

    if _looks_like_listicle(url):
        score -= 0.20
        reasons.append("listicle/aggregator URL")

    if not url:
        score -= 0.15
        reasons.append("no URL")

    return round(max(0.0, min(1.0, score)), 2), reasons


def normalize_exa_result(
    result, query: str = "", constraints=None
) -> dict | None:
    """Convert one Exa result into a venue dict matching the Orkestr venue shape.

    Returns None if the result is unusable (no title/URL, social media, etc).
    All inferences are conservative — uncertain fields default to False/None.
    """
    title = str(_safe_get(result, "title") or "").strip()
    url = str(_safe_get(result, "url") or "").strip()

    if not title or not url:
        return None

    irrelevant_domains = (
        "wikipedia.org", "facebook.com", "instagram.com",
        "twitter.com", "x.com", "youtube.com", "tiktok.com",
    )
    if any(d in url.lower() for d in irrelevant_domains):
        return None

    # Drop results that clearly aren't a place you eat at — event-space rentals,
    # caterers, booking aggregators, blog listicles. Exa sometimes returns these
    # for a "group dinner venue" query and they poison the negotiation.
    if not _looks_like_restaurant(title):
        return None

    raw_highlights = _safe_get(result, "highlights") or []
    if isinstance(raw_highlights, dict):
        raw_highlights = raw_highlights.get("highlights", [])
    if not isinstance(raw_highlights, list):
        raw_highlights = []
    highlights = [str(h).strip() for h in raw_highlights if str(h).strip()]
    highlights_text = " ".join(highlights).lower()

    halal = _infer_halal(title, highlights_text)
    vegetarian = _infer_vegetarian(title, highlights_text)
    near_arcade = _infer_near_arcade(title, highlights_text)
    inferred_price = _infer_price_per_head(highlights_text)
    confidence, confidence_reasons = _confidence_score(title, url, highlights_text, query)

    price_notes = []
    if inferred_price is not None:
        price_per_head = inferred_price
        price_notes.append(f"inferred from highlights ({inferred_price} SGD)")
    else:
        price_per_head = _DEFAULT_PRICE_PER_HEAD
        price_notes.append(f"default estimate ({_DEFAULT_PRICE_PER_HEAD} SGD) — not found in content")
        confidence = round(max(0.0, confidence - 0.05), 2)

    return {
        # Required venue keys (must match data/venues.json shape for planner)
        "id": _slug_id(title),
        "name": title,
        "halal": halal,
        "vegetarian": vegetarian,
        "price_per_head": price_per_head,
        "capacity": _DEFAULT_CAPACITY,
        "opens": _DEFAULT_OPENS,
        "closes": _DEFAULT_CLOSES,
        "near_arcade": near_arcade,
        "lat": None,
        "lng": None,
        # Additive evidence fields (do not break existing venue keys)
        "source": "exa",
        "discovered_by": "exa",
        "source_url": url,
        "source_title": title,
        "source_highlights": highlights[:3],
        "confidence": confidence,
        "confidence_reasons": confidence_reasons,
        "evidence": {
            "price_notes": price_notes,
            "dietary_evidence": {
                "halal_detected": halal,
                "halal_keyword_found": "halal" in _full_text(title, highlights_text),
                "vegetarian_detected": vegetarian,
                "vegetarian_keyword_found": any(
                    w in _full_text(title, highlights_text)
                    for w in ("vegetarian", "vegan", "plant-based")
                ),
            },
        },
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def dedupe_venues(venues: list) -> list:
    seen_names: set = set()
    seen_urls: set = set()
    result = []
    for v in venues:
        if not isinstance(v, dict):
            continue
        name_key = re.sub(r"[^a-z0-9]", "", (v.get("name") or "").lower())
        url_raw = (v.get("source_url") or "").split("?")[0].rstrip("/").lower()

        if not name_key:
            continue
        if name_key in seen_names:
            continue
        if url_raw and url_raw in seen_urls:
            continue

        seen_names.add(name_key)
        if url_raw:
            seen_urls.add(url_raw)
        result.append(v)
    return result


# ---------------------------------------------------------------------------
# Standard response shapes
# ---------------------------------------------------------------------------

def _disabled_resp(query: str) -> dict:
    return {
        "ok": True, "enabled": False, "source": "disabled",
        "query": query, "count": 0, "venues": [],
        "cached": False, "reason": "USE_EXA is not true",
    }


def _missing_key_resp(query: str) -> dict:
    return {
        "ok": True, "enabled": False, "source": "missing_key",
        "query": query, "count": 0, "venues": [],
        "cached": False, "reason": "EXA_API_KEY is not configured",
    }


def _error_resp(query: str) -> dict:
    return {
        "ok": True, "enabled": True, "source": "error",
        "query": query, "count": 0, "venues": [],
        "cached": False, "reason": "Exa discovery failed safely",
    }


# ---------------------------------------------------------------------------
# Main discovery function
# ---------------------------------------------------------------------------

def discover_venues(
    query: str = None,
    constraints: dict = None,
    limit: int = 5,
) -> dict:
    """Search Exa for venue candidates matching the query.

    Never raises. Returns one of the four standard response shapes.
    Secrets are never included in the response.
    """
    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 5
    try:
        hard_cap = int(os.environ.get("EXA_MAX_RESULTS", str(_EXA_MAX_RESULTS_HARD_CAP)))
    except (ValueError, TypeError):
        hard_cap = _EXA_MAX_RESULTS_HARD_CAP
    limit = min(limit, hard_cap)

    if not query or not isinstance(query, str) or not query.strip():
        query = build_venue_query(constraints=constraints)

    if not is_exa_enabled():
        return _disabled_resp(query)

    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        return _missing_key_resp(query)

    ck = _cache_key(query, limit, constraints)
    cached = _cache_get(ck)
    if cached is not None:
        return {**cached, "cached": True}

    try:
        from exa_py import Exa  # lazy import — app boots even if exa-py missing

        exa = Exa(api_key=api_key)
        response = exa.search(
            query,
            num_results=limit,
            type="auto",
            contents={"highlights": True},
        )

        raw_results = _safe_get(response, "results") or []
        if not isinstance(raw_results, list):
            try:
                raw_results = list(raw_results)
            except Exception:
                raw_results = []

        venues = []
        for r in raw_results:
            v = normalize_exa_result(r, query=query, constraints=constraints)
            if v is not None:
                if is_openai_extraction_enabled():
                    enhanced = maybe_extract_with_openai(
                        v["name"], v.get("source_highlights", []), query
                    )
                    if enhanced:
                        if enhanced.get("halal") is not None:
                            v["halal"] = bool(enhanced["halal"])
                        if enhanced.get("vegetarian") is not None:
                            v["vegetarian"] = bool(enhanced["vegetarian"])
                        if isinstance(enhanced.get("price_per_head"), (int, float)):
                            v["price_per_head"] = enhanced["price_per_head"]
                            v["evidence"]["price_notes"].append("enhanced by OpenAI extraction")
                venues.append(v)

        venues = dedupe_venues(venues)
        result = {
            "ok": True,
            "enabled": True,
            "source": "exa",
            "query": query,
            "count": len(venues),
            "venues": venues,
            "cached": False,
            "reason": None,
        }
        _cache_set(ck, result)
        return result

    except Exception:
        return _error_resp(query)


# ---------------------------------------------------------------------------
# Planning supplement (called by core/session.py for non-ORK sessions)
# ---------------------------------------------------------------------------

def _venue_fit_score(venue: dict, personas: list) -> int:
    """How many of the group's real constraints this venue satisfies.

    Mirrors agents/persona.stance so the ranking lines up with how the convener
    actually evaluates plans: budget, halal, vegetarian, no-raw-fish, and the
    meat-eater preference (an all-veg venue is penalised for meat eaters).
    """
    price = venue.get("price_per_head")
    name = str(venue.get("name", "")).lower()
    # Treat a venue as vegetarian-only when its name signals exclusivity (an
    # all-veg place serves no meat), so meat-eaters are penalised against it.
    is_veg_only = bool(venue.get("vegetarian")) and any(
        w in name for w in ("vegan", "vegetarian", "plant-based", "meat-free")
    )
    score = 0
    for p in personas or []:
        c = p.get("constraints") or {}
        diet = [str(d).lower() for d in (c.get("dietary") or [])]
        bmax = c.get("budget_max")
        if not (isinstance(bmax, (int, float)) and isinstance(price, (int, float)) and price > bmax):
            score += 1
        if "halal" in diet and not venue.get("halal"):
            score -= 1
        if ("vegetarian" in diet or "vegan" in diet) and not venue.get("vegetarian"):
            score -= 1
        if "no_raw_fish" in diet and any(w in name for w in ("sushi", "sashimi", "raw")):
            score -= 1
        # Meat-eater (no veg restriction, or asks for meat) vs an all-veg venue.
        wants_meat = ("meat" in str(p.get("freeform", "")).lower()) or not (
            "vegetarian" in diet or "vegan" in diet
        )
        if wants_meat and is_veg_only:
            score -= 1
    return score


def exa_venue_supplements(personas: list, limit: int = 3) -> list:
    """Return Exa-discovered venue dicts for use in planning, best-fit first.

    Returns [] if either USE_EXA or USE_EXA_IN_PLANNING is off, or on any failure.
    The caller (compute_plan in session.py) appends these to the seeded venues list.
    Never raises. Never affects ORK-001 (caller must enforce the sid check).
    """
    if not is_exa_enabled() or not is_exa_planning_enabled():
        return []
    try:
        query = build_venue_query(personas=personas)
        result = discover_venues(query=query, limit=limit)
        venues = result.get("venues", [])
        # Order by how well each real venue fits the group so a genuinely-fitting
        # discovery beats an arbitrary keyword match (e.g. an all-veg place).
        return sorted(venues, key=lambda v: _venue_fit_score(v, personas), reverse=True)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Optional OpenAI extraction (disabled by default)
# ---------------------------------------------------------------------------

def maybe_extract_with_openai(
    title: str,
    highlights: list,
    query: str = "",
) -> dict | None:
    """Optionally enhance venue extraction using OpenAI.

    Returns None (fall back to deterministic) on any failure or when disabled.
    Never runs for ORK-001 (enforcement is in the caller chain).
    Never logs or returns secret values.
    """
    if not is_openai_extraction_enabled():
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        highlights_text = " ".join(str(h) for h in highlights[:5])
        prompt = (
            "Extract venue information from this restaurant content. "
            "Return JSON only with exactly these keys: "
            "name (string), halal (true/false/null), "
            "vegetarian (true/false/null), price_per_head (number in SGD or null), "
            "notes (string). "
            "Only set halal or vegetarian to true if clearly mentioned. "
            "Set to null if uncertain.\n\n"
            f"Title: {title}\n"
            f"Content: {highlights_text}"
        )
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=150,
        )
        parsed = json.loads(response.choices[0].message.content)
        return parsed
    except Exception:
        return None
