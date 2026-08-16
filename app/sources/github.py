import requests
from datetime import datetime, timezone, timedelta
from app.models import Change

API = "https://api.github.com"

def _get(path: str):
    r = requests.get(API + path, timeout=30, headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r.json()

def recent_releases(owner: str, repo: str, since_hours: int = 30) -> list[Change]:
    data = _get(f"/repos/{owner}/{repo}/releases?per_page=20")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    out = []
    for item in data:
        published = item.get("published_at") or item.get("created_at")
        dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None
        if dt and dt < cutoff:
            continue
        out.append(Change(
            source=f"github:{owner}/{repo}",
            title=item["name"] or item["tag_name"],
            url=item["html_url"],
            published_at=dt,
            summary=(item.get("body") or "")[:6000],
            change_type="release",
        ))
    return out

def recent_commits(owner: str, repo: str, since_hours: int = 30) -> list[Change]:
    since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
    data = _get(f"/repos/{owner}/{repo}/commits?since={since}&per_page=30")
    out = []
    for item in data:
        msg = item["commit"]["message"].splitlines()[0]
        out.append(Change(
            source=f"github:{owner}/{repo}",
            title=msg,
            url=item["html_url"],
            published_at=datetime.fromisoformat(item["commit"]["committer"]["date"].replace("Z", "+00:00")),
            summary=item["commit"]["message"][:2000],
            change_type="commit",
        ))
    return out
