#!/usr/bin/env python3
"""
MCP regression guard for BuyWhere.

Calls search_products on the deployed /mcp endpoint with two distinct queries
and asserts the result sets differ AND neither matches a known-bad canned
fallback. Fails the deploy if either assertion fails.

Used to catch the recurring "hardcoded 3-product set returned for all queries"
regressions observed on 2026-06-22 in BUY-55198, BUY-55646, BUY-55752.

Usage:
  python scripts/mcp_regression_guard.py \
    --url https://staging-mcp.buywhere.ai/mcp \
    --api-key $BUYWHERE_API_KEY \
    [--expect-mode]
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

# Known-bad canned fallback sets observed in production regressions on
# 2026-06-22. Update this list when a new canned set is discovered.
KNOWN_BAD_CANNED_TITLES = {
    # 7th regression (BUY-55646, 17:16Z)
    "stan smith",
    "crusher tee",
    # 8th regression (BUY-55752, 20:56Z)
    "plastic serving set & strainer",
    "pump & splash discovery pond",
    "periscope",
    # 9th regression (Relay probe 2026-06-22 21:02Z)
    "ted baker gift card",
    # 10th regression (Relay probe 2026-06-22 21:03Z)
    "soft margaux 12 bag",
    "soft margaux 10 bag",
    "leon t-shirt",
    # Earlier in 2026-06-22
    "ods-agm40e",
    "hk-pc2150",
}

# Two queries that should NEVER return identical first results in a healthy
# system. Both are common, well-represented categories in the catalog.
PROBE_QUERIES = ["laptop", "yoga mat"]


def call_tool(url: str, api_key: str, tool: str, arguments: dict[str, Any], call_id: int) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "mcp-regression-guard/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_titles(envelope: dict[str, Any]) -> list[str]:
    """Walk the JSON-RPC envelope to get result titles, robust to either
    FastMCP's flat {results: [...]} or the server-side MCP handler's
    {content: [{text: '{...}'}]} format.
    """
    result = envelope.get("result")
    if not result:
        return []
    # Format A: direct results array
    if isinstance(result, dict) and "results" in result and isinstance(result["results"], list):
        return [r.get("title", "") for r in result["results"] if isinstance(r, dict)]
    # Format B: content array with text JSON inside
    if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
        for item in result["content"]:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "")
            if not text:
                continue
            try:
                inner = json.loads(text)
            except (ValueError, TypeError):
                continue
            if isinstance(inner, dict) and "results" in inner and isinstance(inner["results"], list):
                return [r.get("title", "") for r in inner["results"] if isinstance(r, dict)]
    return []


def is_canned(title: str) -> bool:
    t = (title or "").lower()
    return any(bad in t for bad in KNOWN_BAD_CANNED_TITLES)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True, help="MCP endpoint URL, e.g. https://api.buywhere.ai/mcp")
    p.add_argument("--api-key", required=True)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    titles_by_query: dict[str, list[str]] = {}
    for i, q in enumerate(PROBE_QUERIES):
        try:
            env = call_tool(args.url, args.api_key, "search_products", {"query": q, "limit": 3}, call_id=i + 1)
        except urllib.error.HTTPError as e:
            print(f"FAIL: HTTP {e.code} calling search_products({q!r}): {e.reason}", file=sys.stderr)
            return 2
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"FAIL: transport/parse error on query {q!r}: {e}", file=sys.stderr)
            return 2
        if "error" in env:
            print(f"FAIL: JSON-RPC error on query {q!r}: {env['error']}", file=sys.stderr)
            return 2
        titles = extract_titles(env)
        titles_by_query[q] = titles
        if not args.quiet:
            print(f"  query {q!r}: {len(titles)} results, first = {titles[0] if titles else '(empty)'!r}")

    failures: list[str] = []

    # Assertion 1: result sets differ between two distinct queries
    t_a = titles_by_query[PROBE_QUERIES[0]]
    t_b = titles_by_query[PROBE_QUERIES[1]]
    if t_a == t_b and t_a:
        failures.append(
            f"result set for {PROBE_QUERIES[0]!r} == result set for {PROBE_QUERIES[1]!r} "
            f"(both = {t_a!r}). Hardcoded fallback regression."
        )

    # Assertion 2: first result of each query is not in known-bad canned set
    for q, titles in titles_by_query.items():
        if not titles:
            failures.append(f"query {q!r} returned 0 results")
            continue
        first = titles[0]
        if is_canned(first):
            failures.append(f"query {q!r} first result {first!r} matches known-bad canned fallback")

    if failures:
        print("\nMCP REGRESSION GUARD FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("\nMCP REGRESSION GUARD PASS: search_products returns query-dependent, non-canned results.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
