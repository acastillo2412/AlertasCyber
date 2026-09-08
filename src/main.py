import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config, telegram, translate
from src.sources import nvd, rss
from src.store import SeenStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("alertacyber")


def main() -> int:
    vendors = config.load_vendors()
    store = SeenStore(config.SEEN_FILE)

    total_sent = 0
    total_errors = 0

    for vendor_key, vendor in vendors.items():
        label = vendor.get("label", vendor_key)
        items = []

        try:
            items.extend(
                nvd.fetch_new_cves(
                    keywords=vendor.get("nvd_keywords", []),
                    lookback_days=config.LOOKBACK_DAYS,
                    api_key=config.NVD_API_KEY,
                )
            )
        except Exception:
            log.exception("Error consultando NVD para %s", label)
            total_errors += 1

        for feed_url in vendor.get("rss_feeds", []):
            try:
                items.extend(rss.fetch_new_entries(feed_url, config.LOOKBACK_DAYS))
            except Exception:
                log.exception("Error consultando RSS %s para %s", feed_url, label)
                total_errors += 1

        new_items = [item for item in items if not store.has(item["id"])]
        new_items.sort(key=lambda i: i.get("published") or "")

        for item in new_items:
            try:
                item["description"] = translate.to_spanish(item.get("description", ""))
                text = telegram.format_message(label, item)
                telegram.send_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, text)
                store.add(item["id"])
                total_sent += 1
                log.info("Enviado [%s] %s", label, item["id"])
            except Exception:
                log.exception("Error enviando a Telegram [%s] %s", label, item.get("id"))
                total_errors += 1

    store.save()
    log.info("Resumen: %d alertas nuevas enviadas, %d errores.", total_sent, total_errors)
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
