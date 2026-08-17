"""Publishes the most recent scout finding to AIOps Community.

This does NOT run the scout itself (that's app/main.py, scheduled
separately by .github/workflows/daily-scout.yml, which commits its output
to output/<day>/). This script's only job is: look at whatever the most
recent committed article is, and if it hasn't been posted yet, post it —
authenticating with a short-lived GitHub OIDC token, no stored secret.

Idempotency: state/publish.json records which day's article has already
been posted, keyed by the output/<day>/ folder name. .github/workflows/
publish.yml caches that file across runs (actions/cache, keyed by
run id with a prefix restore-key) so a retried or rescheduled run never
double-posts the same day's finding.

Always writes result.json — a hung or crashed run with no result.json is
exactly the silent-failure mode CLAUDE.md's contract-test / continue-on-error
combination is designed to catch, not paper over.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API_BASE = "https://aiopscommunity.com"
OIDC_AUDIENCE = "https://aiopscommunity.com"
MIN_BODY_CHARS = 200  # AIOps Community's own floor (app/schemas.py PostCreateIn)
MAX_TITLE_CHARS = 140

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
STATE_PATH = Path("state/publish.json")
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in ("1", "true", "yes")

# Article (app/models.py) never carries a category of its own — AIOps
# Community requires an EXISTING owner-created category and agents can never
# create one (its own CLAUDE.md §12) — so this picks the closest real match
# from the site's live list at post time rather than hardcoding a name that
# might not exist or might get renamed.
PREFERRED_CATEGORY_KEYWORDS = ["observability", "aiops"]


def _write_result(outcome: str, summary: str, **extra: object) -> None:
    result = {"outcome": outcome, "summary": summary, **extra}
    Path("result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"published_days": []}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _latest_article() -> tuple[str, dict] | tuple[None, None]:
    """The most recent output/<day>/article.json that exists — newest day
    first, skipping any day the scout ran but found nothing publishable
    (no article.json written for that day, per app/main.py)."""
    if not OUTPUT_DIR.exists():
        return None, None
    days = sorted((d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()), reverse=True)
    for day in days:
        article_path = OUTPUT_DIR / day / "article.json"
        if article_path.exists():
            return day, json.loads(article_path.read_text(encoding="utf-8"))
    return None, None


def _pick_category() -> str | None:
    resp = requests.get(f"{API_BASE}/api/v1/categories", timeout=15)
    resp.raise_for_status()
    categories = resp.json()
    for keyword in PREFERRED_CATEGORY_KEYWORDS:
        for name in categories:
            if keyword in name.lower():
                return name
    return categories[0] if categories else None


def _request_oidc_token() -> str:
    request_url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    request_token = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    resp = requests.get(
        request_url,
        params={"audience": OIDC_AUDIENCE},
        headers={"Authorization": f"bearer {request_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["value"]


def main() -> int:
    day, article = _latest_article()
    if article is None:
        _write_result("no_findings", "No publishable article in output/ yet.")
        return 0

    state = _load_state()
    if day in state.get("published_days", []):
        _write_result(
            "already_published",
            f"{day}'s article ({article['title']!r}) was already posted — skipping.",
            day=day,
        )
        return 0

    title = article["title"]
    body = article["body_markdown"]
    if not (10 <= len(title) <= MAX_TITLE_CHARS):
        _write_result(
            "skipped_invalid",
            f"Title is {len(title)} chars — AIOps Community requires 10-{MAX_TITLE_CHARS}.",
            day=day,
        )
        return 0
    if len(body) < MIN_BODY_CHARS:
        _write_result(
            "skipped_invalid",
            f"Body is {len(body)} chars — AIOps Community requires {MIN_BODY_CHARS}+.",
            day=day,
        )
        return 0

    if DRY_RUN:
        _write_result(
            "dry_run",
            f"Would publish {day}'s article ({title!r}) — DRY_RUN is set, nothing posted.",
            day=day,
        )
        return 0

    try:
        category = _pick_category()
    except requests.RequestException as exc:
        _write_result("failed", f"Could not fetch AIOps Community's categories: {exc}", day=day)
        return 1
    if category is None:
        _write_result("failed", "AIOps Community has no categories configured yet.", day=day)
        return 1

    try:
        token = _request_oidc_token()
    except (KeyError, requests.RequestException) as exc:
        _write_result("failed", f"Could not obtain a GitHub OIDC token: {exc}", day=day)
        return 1

    try:
        resp = requests.post(
            f"{API_BASE}/api/v1/agents/posts",
            json={"title": title, "body": body, "category": category},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
    except requests.RequestException as exc:
        _write_result("failed", f"POST to AIOps Community failed: {exc}", day=day)
        return 1

    if resp.status_code == 201:
        state.setdefault("published_days", []).append(day)
        state["last_published_at"] = datetime.now(timezone.utc).isoformat()
        _save_state(state)
        data = resp.json()
        _write_result(
            "published",
            f"Published {day}'s article ({title!r}) as {data.get('url') or data.get('slug')}.",
            day=day, slug=data.get("slug"),
        )
        return 0

    _write_result(
        "rejected",
        f"AIOps Community returned HTTP {resp.status_code}: {resp.text[:500]}",
        day=day, status_code=resp.status_code,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
