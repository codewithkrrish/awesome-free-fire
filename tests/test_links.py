"""Tests for the awesome-free-fire list.

The list is the product here, so the tests guard what matters: every
entry is well-formed, nothing banned sneaks in, and the README and the
data file never drift apart.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINKS_FILE = REPO_ROOT / "links.json"
README_FILE = REPO_ROOT / "README.md"

ALLOWED_CATEGORIES = {
    "Official",
    "Stats and profile trackers",
    "Sensitivity and settings",
    "Tournaments and guilds",
    "Content creation",
    "Aim and practice",
    "News, wikis and community",
}

ALLOWED_COSTS = {"Free", "Free to join", "Free with paid tier"}

# Anything that can get an account banned, or smells like a scam, must
# never appear in this list. Checked against name, note and URL.
BANNED_WORDS = (
    "mod apk",
    "mod menu",
    "injector",
    "panel",
    "diamond generator",
    "free diamonds",
    "unlimited diamonds",
    "hack",
    "cheat",
)

REQUIRED_FIELDS = ("name", "url", "category", "cost", "note")


@pytest.fixture(scope="module")
def links_data() -> dict:
    return json.loads(LINKS_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries(links_data) -> list[dict]:
    assert isinstance(links_data.get("entries"), list)
    return links_data["entries"]


def test_links_file_has_entries(entries):
    assert len(entries) >= 20, "a list this thin is not worth starring"


def test_every_entry_has_required_fields(entries):
    for entry in entries:
        for field in REQUIRED_FIELDS:
            assert field in entry, f"{entry.get('name', entry)} is missing {field}"
            assert isinstance(entry[field], str) and entry[field].strip(), (
                f"{entry['name']}: {field} is empty"
            )


def test_categories_are_known(entries):
    for entry in entries:
        assert entry["category"] in ALLOWED_CATEGORIES, (
            f"{entry['name']}: unknown category {entry['category']!r}"
        )


def test_cost_labels_are_known(entries):
    for entry in entries:
        assert entry["cost"] in ALLOWED_COSTS, (
            f"{entry['name']}: unknown cost label {entry['cost']!r}"
        )


def test_urls_are_valid_and_unique(entries):
    seen: set[str] = set()
    for entry in entries:
        parsed = urlparse(entry["url"])
        assert parsed.scheme in ("http", "https"), f"{entry['name']}: bad scheme"
        assert parsed.netloc, f"{entry['name']}: no host in URL"
        assert entry["url"] not in seen, f"duplicate URL: {entry['url']}"
        seen.add(entry["url"])


def test_names_are_unique(entries):
    names = [entry["name"].lower() for entry in entries]
    assert len(names) == len(set(names)), "duplicate entry names"


def test_notes_are_real_sentences(entries):
    # A one-word note means nobody actually looked at the site.
    for entry in entries:
        assert len(entry["note"]) >= 40, f"{entry['name']}: note is too thin"
        assert len(entry["note"]) <= 280, f"{entry['name']}: note is too long"


def test_no_banned_words(entries):
    for entry in entries:
        haystack = f"{entry['name']} {entry['note']} {entry['url']}".lower()
        for word in BANNED_WORDS:
            assert word not in haystack, (
                f"{entry['name']}: banned word {word!r} — this list is legit-only"
            )


def test_every_category_has_entries(entries):
    present = {entry["category"] for entry in entries}
    missing = ALLOWED_CATEGORIES - present
    assert not missing, f"empty categories: {sorted(missing)}"


def test_readme_lists_every_link(entries):
    readme = README_FILE.read_text(encoding="utf-8")
    missing = [e["name"] for e in entries if e["url"] not in readme]
    assert not missing, f"links.json entries missing from README: {missing}"


def test_readme_mentions_the_rules():
    readme = README_FILE.read_text(encoding="utf-8").lower()
    assert "legit" in readme
    assert "diamond generator" in readme or "no mods" in readme


# --- link checker unit tests (no network: urlopen is stubbed) -------------

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_links  # noqa: E402


class FakeResponse:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_checker_marks_200_ok(monkeypatch):
    monkeypatch.setattr(
        check_links.urllib.request, "urlopen",
        lambda *a, **k: FakeResponse(200),
    )
    assert check_links.check_url("https://example.com") == ("ok", "HTTP 200")


def test_checker_marks_403_guarded_not_dead(monkeypatch):
    def raise_403(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.com", 403, "Forbidden", None, None)

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_403)
    status, _ = check_links.check_url("https://example.com")
    assert status == "guarded"


def test_checker_marks_404_dead(monkeypatch):
    def raise_404(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.com", 404, "Not Found", None, None)

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_404)
    status, _ = check_links.check_url("https://example.com")
    assert status == "dead"


def test_checker_marks_dns_failure_dead(monkeypatch):
    def raise_dns(*args, **kwargs):
        raise urllib.error.URLError("Name or service not known")

    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_dns)
    status, _ = check_links.check_url("https://no-such-host.example")
    assert status == "dead"


def test_checker_loads_links_file():
    entries = check_links.load_links()
    assert len(entries) >= 20
