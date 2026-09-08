"""Lector generico de feeds RSS de avisos de seguridad de fabricantes."""

from calendar import timegm
from datetime import datetime, timedelta, timezone

import feedparser


def fetch_new_entries(feed_url: str, lookback_days: int, keywords: list[str] | None = None) -> list[dict]:
    """Si se pasan keywords, solo se devuelven entradas cuyo titulo o resumen
    contenga alguna de ellas (evita ruido de feeds que cubren todo el fabricante)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    parsed = feedparser.parse(feed_url)
    keywords_lower = [k.lower() for k in keywords] if keywords else None

    entries = []
    for entry in parsed.entries:
        if keywords_lower:
            haystack = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
            if not any(k in haystack for k in keywords_lower):
                continue

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
