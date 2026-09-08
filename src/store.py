import json
from pathlib import Path


class SeenStore:
    """Registro de IDs (CVE o entradas RSS) ya notificados, para evitar duplicados."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ids = self._load()

    def _load(self) -> set:
        if not self.path.exists():
            return set()
        with open(self.path, "r", encoding="utf-8") as f:
            return set(json.load(f))

    def has(self, item_id: str) -> bool:
        return item_id in self._ids

    def add(self, item_id: str) -> None:
        self._ids.add(item_id)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(sorted(self._ids), f, ensure_ascii=False, indent=2)
