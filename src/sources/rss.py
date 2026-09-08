"""Lector generico de feeds RSS de avisos de seguridad de fabricantes."""

from calendar import timegm
from datetime import datetime, timedelta, timezone

import feedparser


def fetch_new_entries(feed_url: str, lookback_days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    parsed = feedparser.parse(feed_url)

    entries = []
    for entry in parsed.entries:
        published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_struct:
            published_dt = datetime.fromtimestamp(timegm(published_struct), tz=timezone.utc)
            if published_dt < cutoff:
                continue
            published_iso = published_dt.isoformat()
        else:
            # Sin fecha fiable: se incluye para no perder el aviso, se dedupe por id igualmente.
            published_iso = None

        entry_id = entry.get("id") or entry.get("link")
        if not entry_id:
            continue

        entries.append(
            {
                "id": entry_id,
                "title": entry.get("title", feed_url),
                "description": entry.get("summary", ""),
                "severity": "N/D",
                "score": None,
                "published": published_iso,
                "url": entry.get("link", feed_url),
                "source": "RSS",
            }
        )

    return entries
