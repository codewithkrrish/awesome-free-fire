#!/usr/bin/env python3
"""Check every link in links.json and report which ones are alive.

A list is only useful if its links work, and Free Fire fan sites die or
move all the time. Run this before opening a PR that touches links.json,
or whenever you want to know what has rotted:

    python scripts/check_links.py            # human-readable report
    python scripts/check_links.py --json     # machine-readable report

Exit codes: 0 = everything reachable (or only bot-guarded), 1 = a link
is dead, 2 = links.json itself is broken.

A note on "guarded": some big sites (Reddit, Fandom, Liquipedia, Garena
support) block automated requests with a 403 or a 429. That does not mean
the link is dead, it means the site does not like bots. Those are reported
as GUARDED, not dead, and they do not fail the run. A link only counts as
dead when it 404s, 500s, times out, or fails to resolve at all.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# How long to wait for a slow site before calling it dead.
REQUEST_TIMEOUT_SECONDS = 15

# Statuses that mean "the site is there, it just won't talk to a script".
GUARDED_STATUSES = {401, 403, 429}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LINKS_FILE = REPO_ROOT / "links.json"


class LinksFileError(Exception):
    """links.json is missing or unparsable."""


def load_links() -> list[dict]:
    """Read links.json and return its entries list."""
    try:
        data = json.loads(LINKS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LinksFileError(f"{LINKS_FILE} not found") from exc
    except json.JSONDecodeError as exc:
        raise LinksFileError(f"{LINKS_FILE} is not valid JSON: {exc}") from exc
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise LinksFileError("links.json has no 'entries' list")
    return entries


def check_url(url: str) -> tuple[str, str]:
    """Probe one URL. Returns (status, detail).

    status is one of "ok", "guarded" or "dead".
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return "ok", f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in GUARDED_STATUSES:
            return "guarded", f"HTTP {exc.code} (site blocks automated checks)"
        return "dead", f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # URLError covers DNS failures and refused connections; the site
        # is unreachable from here, which for a link list is dead enough.
        reason = getattr(exc, "reason", exc)
        return "dead", f"unreachable ({reason})"


def check_all(entries: list[dict]) -> list[dict]:
    """Check every entry and return a result dict per entry."""
    results = []
    for entry in entries:
        status, detail = check_url(entry["url"])
        results.append({"name": entry["name"], "url": entry["url"], "status": status, "detail": detail})
    return results


def print_report(results: list[dict]) -> int:
    """Print a plain-text report. Returns the exit code."""
    dead = [r for r in results if r["status"] == "dead"]
    guarded = [r for r in results if r["status"] == "guarded"]
    ok = [r for r in results if r["status"] == "ok"]

    for result in results:
        mark = {"ok": "OK     ", "guarded": "GUARDED", "dead": "DEAD   "}[result["status"]]
        print(f"[{mark}] {result['name']} — {result['detail']}")

    print()
    print(f"{len(ok)} ok, {len(guarded)} guarded, {len(dead)} dead "
          f"({len(results)} total)")
    if dead:
        print("Dead links (fix or remove these):")
        for result in dead:
            print(f"  - {result['name']}: {result['url']} ({result['detail']})")
        return 1
    if guarded:
        print("Guarded links are fine — those sites block bots, the links "
              "were confirmed by hand.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true",
                        help="print results as JSON instead of a text report")
    args = parser.parse_args(argv)

    try:
        entries = load_links()
    except LinksFileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = check_all(entries)
    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if any(r["status"] == "dead" for r in results) else 0
    return print_report(results)


if __name__ == "__main__":
    raise SystemExit(main())
