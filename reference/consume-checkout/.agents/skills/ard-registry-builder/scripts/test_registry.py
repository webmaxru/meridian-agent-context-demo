#!/usr/bin/env python3
"""Probe a live ARD Agent Registry REST API for spec conformance.

Exercises the endpoints defined in the ARD OpenAPI specification:
  * POST /search   (REQUIRED, ARD sec 7.2)  - semantic search
  * GET  /agents   (OPTIONAL, ARD sec 7.4)  - deterministic listing
  * POST /explore  (OPTIONAL, ARD sec 7.3)  - facet aggregation (501 if unsupported)

For each endpoint it checks HTTP status, the response envelope shape, and - for
search - that every result is a well-formed catalog entry carrying a relevance
`score` (0-100) and a `source`. It also verifies the registry rejects a malformed
request with a 4xx error carrying `errorCode` + `message`.

Usage:
    python test_registry.py http://localhost:9010/api
    python test_registry.py https://registry.acme.com/api/v1 --query "weather forecast" --json

Exit codes: 0 = all required checks passed, 1 = a required check failed, 2 = could not reach server.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

URN_RE = re.compile(r"^urn:air:[a-zA-Z0-9.-]+(:[a-zA-Z0-9._-]+)+$")
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


class Check:
    __slots__ = ("name", "status", "required", "detail")

    def __init__(self, name: str, status: str, required: bool, detail: str):
        self.name, self.status, self.required, self.detail = name, status, required, detail

    def as_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "required": self.required, "detail": self.detail}


def http_json(method: str, url: str, body: dict | None, timeout: float):
    """Return (status_code, parsed_body_or_text, transport_error)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "ard-registry-builder/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _parse(resp.read()), None
    except urllib.error.HTTPError as exc:
        return exc.code, _parse(exc.read()), None
    except Exception as exc:  # noqa: BLE001  (URLError, timeout, conn refused, ...)
        return None, None, str(exc)


def _parse(raw: bytes):
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def validate_result_item(item) -> list[str]:
    """Return a list of problems for one search result item (empty == valid)."""
    problems: list[str] = []
    if not isinstance(item, dict):
        return ["result is not an object"]
    for field in ("identifier", "displayName", "type"):
        if not isinstance(item.get(field), str):
            problems.append(f"missing/invalid '{field}'")
    ident = item.get("identifier")
    if isinstance(ident, str) and not URN_RE.match(ident):
        problems.append(f"identifier '{ident}' is not a valid urn:air: URN")
    has_url, has_data = "url" in item, "data" in item
    if has_url == has_data:
        problems.append("must carry exactly one of 'url' or 'data'")
    score = item.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or not (0 <= score <= 100):
        problems.append("'score' must be an integer in 0..100")
    if not isinstance(item.get("source"), str):
        problems.append("missing 'source' (registry base URL)")
    return problems


def run(base: str, query_text: str, timeout: float) -> list[Check]:
    base = base.rstrip("/")
    checks: list[Check] = []

    # --- POST /search (REQUIRED) ---
    status, body, err = http_json("POST", f"{base}/search",
                                  {"query": {"text": query_text}, "pageSize": 5}, timeout)
    if err is not None:
        checks.append(Check("search:reachable", FAIL, True, f"could not reach {base}/search: {err}"))
        return checks
    if status == 200:
        checks.append(Check("search:status-200", PASS, True, "POST /search returned 200"))
        if isinstance(body, dict) and isinstance(body.get("results"), list):
            checks.append(Check("search:results-array", PASS, True,
                                f"response has a 'results' array ({len(body['results'])} item(s))"))
            problems = []
            for idx, item in enumerate(body["results"]):
                for p in validate_result_item(item):
                    problems.append(f"results[{idx}]: {p}")
            if problems:
                checks.append(Check("search:result-shape", FAIL, True, "; ".join(problems[:8])))
            else:
                checks.append(Check("search:result-shape", PASS, True,
                                    "every result is a valid catalog entry with score(0-100) + source"))
            if "referrals" in body and not isinstance(body["referrals"], list):
                checks.append(Check("search:referrals-type", FAIL, False, "'referrals' present but is not an array"))
        else:
            checks.append(Check("search:results-array", FAIL, True,
                                "200 response is missing a 'results' array (ARD sec 7.2 envelope)"))
    else:
        checks.append(Check("search:status-200", FAIL, True,
                            f"POST /search returned {status}, expected 200"))

    # --- POST /search malformed (REQUIRED: must reject) ---
    status, body, err = http_json("POST", f"{base}/search", {"pageSize": 5}, timeout)  # no query.text
    if err is not None:
        checks.append(Check("search:rejects-bad-request", SKIP, False, f"transport error: {err}"))
    elif status == 400:
        ok = isinstance(body, dict) and isinstance(body.get("errorCode"), str) and isinstance(body.get("message"), str)
        checks.append(Check("search:rejects-bad-request", PASS if ok else FAIL, True,
                            "400 with errorCode+message" if ok else "400 but body lacks errorCode/message (ARD Appendix B)"))
    elif status is not None and 400 <= status < 500:
        checks.append(Check("search:rejects-bad-request", FAIL, False,
                            f"malformed request rejected with {status}; spec prescribes 400 INVALID_ARGUMENT"))
    else:
        checks.append(Check("search:rejects-bad-request", FAIL, True,
                            f"malformed request returned {status}; a missing query.text MUST be rejected (4xx)"))

    # --- GET /agents (OPTIONAL) ---
    status, body, err = http_json("GET", f"{base}/agents?pageSize=5", None, timeout)
    if err is not None:
        checks.append(Check("agents:list", SKIP, False, f"transport error: {err}"))
    elif status == 200 and isinstance(body, dict) and isinstance(body.get("items"), list):
        problems = []
        for idx, item in enumerate(body["items"]):
            if not isinstance(item, dict) or not isinstance(item.get("identifier"), str):
                problems.append(f"items[{idx}] is not a catalog entry")
        checks.append(Check("agents:list", PASS if not problems else FAIL, False,
                            f"GET /agents returned {len(body['items'])} item(s)" if not problems else "; ".join(problems[:5])))
    elif status in (404, 405, 501):
        checks.append(Check("agents:list", SKIP, False, f"GET /agents not implemented (HTTP {status}) - optional (sec 7.4)"))
    else:
        checks.append(Check("agents:list", FAIL, False, f"GET /agents returned {status} without a valid 'items' envelope"))

    # --- POST /explore (OPTIONAL) ---
    status, body, err = http_json("POST", f"{base}/explore",
                                  {"resultType": {"facets": [{"field": "type"}]}}, timeout)
    if err is not None:
        checks.append(Check("explore:facets", SKIP, False, f"transport error: {err}"))
    elif status == 501:
        checks.append(Check("explore:facets", SKIP, False, "POST /explore returns 501 - optional and not implemented (sec 7.3)"))
    elif status == 200 and isinstance(body, dict) and body.get("resultType") == "facets" and isinstance(body.get("facets"), dict):
        checks.append(Check("explore:facets", PASS, False, "POST /explore returned a valid facets envelope"))
    else:
        checks.append(Check("explore:facets", FAIL, False, f"POST /explore returned {status} without a valid facets envelope"))

    return checks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Probe a live ARD registry REST API for conformance.")
    ap.add_argument("base_url", help="Base URL of the registry API (e.g. http://localhost:9010/api).")
    ap.add_argument("--query", default="weather forecast", help="Search text to send to POST /search.")
    ap.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds.")
    ap.add_argument("--json", action="store_true", help="Emit results as JSON.")
    args = ap.parse_args(argv)

    checks = run(args.base_url, args.query, args.timeout)
    required_failed = sum(1 for c in checks if c.required and c.status == FAIL)
    unreachable = any(c.name == "search:reachable" and c.status == FAIL for c in checks)

    if args.json:
        print(json.dumps({
            "base_url": args.base_url,
            "ok": required_failed == 0 and not unreachable,
            "summary": {
                "passed": sum(1 for c in checks if c.status == PASS),
                "failed": sum(1 for c in checks if c.status == FAIL),
                "skipped": sum(1 for c in checks if c.status == SKIP),
                "required_failed": required_failed,
            },
            "checks": [c.as_dict() for c in checks],
        }, indent=2))
    else:
        print(f"ARD registry conformance: {args.base_url}\n")
        for c in checks:
            tag = "(required)" if c.required else "(optional)"
            print(f"{c.status:<4} {c.name:<28} {tag}  {c.detail}")
        verdict = "FAIL" if (required_failed or unreachable) else "PASS"
        print(f"\nResult: {verdict} - {required_failed} required check(s) failed")

    if unreachable:
        return 2
    return 1 if required_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
