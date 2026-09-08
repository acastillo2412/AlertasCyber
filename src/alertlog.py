"""Historial de alertas enviadas, usado para construir los resumenes periodicos."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

RETENTION_DAYS = 40


def append(path: Path, vendor: str, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vendor": vendor,
        "id": item.get("id"),
        "title": item.get("title"),
        "severity": (item.get("severity") or "N/D").upper(),
        "score": item.get("score"),
        "url": item.get("url"),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def load_recent(path: Path, since_hours: float) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    result = []
    for entry in _read_all(path):
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            result.append(entry)
    return result


def prune(path: Path, retention_days: int = RETENTION_DAYS) -> None:
    if not path.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    kept = []
    for entry in _read_all(path):
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            kept.append(json.dumps(entry, ensure_ascii=False))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(kept) + ("\n" if kept else ""))
