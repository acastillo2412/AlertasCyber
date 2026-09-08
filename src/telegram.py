import re
import time

import requests

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def _strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
    "N/D": "⚪",
    "DESCONOCIDA": "⚪",
}


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_message(vendor_label: str, item: dict) -> str:
    emoji = SEVERITY_EMOJI.get((item.get("severity") or "").upper(), "⚪")
    score = item.get("score")
    score_txt = f" ({score})" if score is not None else ""
    description = _strip_html(item.get("description", ""))
    if len(description) > 500:
        description = description[:497] + "..."

    lines = [
        f"{emoji} <b>{escape_html(vendor_label)}</b> — {escape_html(item['title'])}",
        f"Severidad: {escape_html(item.get('severity', 'N/D'))}{score_txt} | Fuente: {item.get('source')}",
    ]
    if description:
        lines.append(escape_html(description))
    lines.append(item.get("url", ""))
    return "\n".join(lines)


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=15,
    )
    resp.raise_for_status()
    time.sleep(1.1)  # limite de Telegram: ~1 mensaje/segundo por chat
