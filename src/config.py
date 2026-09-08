import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Falta la variable de entorno {name}. Copia .env.example a .env y complétala."
        )
    return value


TELEGRAM_BOT_TOKEN = _require_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _require_env("TELEGRAM_CHAT_ID")
NVD_API_KEY = os.environ.get("NVD_API_KEY", "").strip() or None
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "3"))

VENDORS_FILE = ROOT_DIR / "config" / "vendors.json"
SEEN_FILE = ROOT_DIR / "data" / "seen.json"
ALERT_LOG_FILE = ROOT_DIR / "data" / "alert_log.jsonl"


def load_vendors() -> dict:
    with open(VENDORS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
