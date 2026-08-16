import json
from datetime import datetime, timezone

from app.config import OUTPUT_DIR, LOOKBACK_HOURS
from app.sources.github import recent_releases, recent_commits
from app.sources.rss import recent_rss
from app.intelligence import investigate
from app.article import write_article

TARGETS = [
    ("kubernetes", "kubernetes"),
    ("open-telemetry", "opentelemetry-collector"),
]

def collect():
    changes = []
    for owner, repo in TARGETS:
        changes.extend(recent_releases(owner, repo, LOOKBACK_HOURS))
        changes.extend(recent_commits(owner, repo, LOOKBACK_HOURS))
    changes.extend(recent_rss(since_hours=LOOKBACK_HOURS))
    unique = {c.url: c for c in changes if c.url}
    return list(unique.values())

def run():
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    out = OUTPUT_DIR / day
    out.mkdir(parents=True, exist_ok=True)

    changes = collect()
    (out / "sources.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in changes], indent=2),
        encoding="utf-8",
    )

    finding = investigate(changes) if changes else None
    article = write_article(finding, changes) if finding and finding.publishable else None

    if finding:
        (out / "findings.json").write_text(
            json.dumps(finding.model_dump(mode="json"), indent=2), encoding="utf-8"
        )
    if article:
        (out / "article.json").write_text(
            json.dumps(article.model_dump(mode="json"), indent=2), encoding="utf-8"
        )
        (out / "article.md").write_text(article.body_markdown, encoding="utf-8")

    run_record = {
        "run_at": now.isoformat(),
        "lookback_hours": LOOKBACK_HOURS,
        "changes_detected": len(changes),
        "publishable_finding": bool(finding and finding.publishable),
        "article_generated": bool(article),
        "decision": "published_artifact" if article else "no_article",
    }
    (out / "run.json").write_text(json.dumps(run_record, indent=2), encoding="utf-8")
    print(json.dumps(run_record, indent=2))

if __name__ == "__main__":
    run()
