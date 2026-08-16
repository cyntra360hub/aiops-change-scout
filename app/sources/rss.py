from datetime import datetime, timezone, timedelta
import feedparser
from app.models import Change

DEFAULT_FEEDS = [
    ("CNCF Blog", "https://www.cncf.io/feed/"),
]

def recent_rss(feeds=DEFAULT_FEEDS, since_hours=30) -> list[Change]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    out = []
    for source_name, url in feeds:
        feed = feedparser.parse(url)
        for item in feed.entries[:50]:
            published = None
            if getattr(item, "published_parsed", None):
                published = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
            if published and published < cutoff:
                continue
            out.append(Change(
                source=source_name,
                title=item.get("title", ""),
                url=item.get("link", ""),
                published_at=published,
                summary=item.get("summary", "")[:6000],
                change_type="announcement",
            ))
    return out
