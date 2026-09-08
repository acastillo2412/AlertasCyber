"""Genera un resumen (periodico o semanal) de las alertas ya enviadas y lo
manda a Telegram, destacando las criticas y si consta que se explotan
activamente (CISA KEV) para orientar si conviene actuar ya o no es urgente."""

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import alertlog, config, kev, telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("alertacyber-resumen")


def build_message(entries: list[dict], kev_ids: set[str], period_label: str) -> str:
    critical = [e for e in entries if e.get("severity") == "CRITICAL"]

    lines = [f"<b>📋 Resumen AlertaCyber — {period_label}</b>"]
    lines.append(f"Alertas enviadas: {len(entries)} | Críticas: {len(critical)}")

    if entries:
        by_vendor = Counter(e.get("vendor", "?") for e in entries)
        lines.append("")
        lines.append("Por fabricante: " + ", ".join(f"{v} ({n})" for v, n in by_vendor.most_common()))

    lines.append("")
    if not critical:
        lines.append("✅ No hay vulnerabilidades críticas en este periodo. No es necesario actuar de forma urgente.")
    else:
        exploited = [e for e in critical if e.get("id") in kev_ids]
        if exploited:
            lines.append(
                f"🚨 <b>Acción requerida:</b> {len(exploited)} de {len(critical)} vulnerabilidad(es) "
                "crítica(s) consta(n) como explotada(s) activamente (CISA KEV). Priorizar el parcheo ya."
            )
        else:
            lines.append(
                f"⚠️ Hay {len(critical)} vulnerabilidad(es) crítica(s), pero ninguna consta como explotada "
                "activamente todavía. Se recomienda planificar el parcheo, sin ser urgencia inmediata."
            )
        lines.append("")
        lines.append("<b>Detalle de críticas:</b>")
        for e in critical:
            tag = " 🚨 EXPLOTADA (KEV)" if e.get("id") in kev_ids else ""
            score_txt = f" ({e['score']})" if e.get("score") is not None else ""
            lines.append(
                f"• [{telegram.escape_html(e.get('vendor', ''))}] "
                f"{telegram.escape_html(e.get('id', ''))}{score_txt}{tag}\n  {e.get('url', '')}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly", action="store_true", help="Resumen semanal (7 dias) en vez del periodico")
    parser.add_argument("--hours", type=float, default=12, help="Horas hacia atras a resumir (ignorado si --weekly)")
    args = parser.parse_args()

    if args.weekly:
        hours = 24 * 7
        period_label = "resumen semanal"
    else:
        hours = args.hours
        period_label = f"últimas {int(hours)} horas"

    entries = alertlog.load_recent(config.ALERT_LOG_FILE, since_hours=hours)
    kev_ids = kev.fetch_kev_ids()
    text = build_message(entries, kev_ids, period_label)

    telegram.send_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, text)
    log.info("Resumen enviado (%s): %d alertas, %d criticas.", period_label, len(entries),
              len([e for e in entries if e.get("severity") == "CRITICAL"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
