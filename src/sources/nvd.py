"""Cliente minimo para la API 2.0 de NVD (CVE), filtrado por palabra clave."""

import time
from datetime import datetime, timedelta, timezone

import requests

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _severity_from_cve(cve: dict) -> tuple[str, float | None]:
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if entries:
            data = entries[0].get("cvssData", {})
            score = data.get("baseScore")
            severity = data.get("baseSeverity") or entries[0].get("baseSeverity")
            return (severity or "DESCONOCIDA", score)
    return ("DESCONOCIDA", None)


def _description(cve: dict) -> str:
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en":
            return d.get("value", "")
    return ""


def fetch_new_cves(keywords: list[str], lookback_days: int, api_key: str | None) -> list[dict]:
    """Devuelve CVEs publicados en la ventana de tiempo que coinciden con alguna keyword."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    pub_start = start.strftime("%Y-%m-%dT%H:%M:%S.000")
    pub_end = end.strftime("%Y-%m-%dT%H:%M:%S.000")

    headers = {"apiKey": api_key} if api_key else {}
    delay = 0.7 if api_key else 6.5  # respeta el limite de solicitudes de NVD

    results = {}
    for keyword in keywords:
        params = {
            "keywordSearch": keyword,
            "pubStartDate": pub_start,
            "pubEndDate": pub_end,
            "resultsPerPage": 200,
        }
        resp = requests.get(NVD_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id")
            if not cve_id or cve_id in results:
                continue
            severity, score = _severity_from_cve(cve)
            results[cve_id] = {
                "id": cve_id,
                "title": cve_id,
                "description": _description(cve),
                "severity": severity,
                "score": score,
                "published": cve.get("published"),
                "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                "source": "NVD",
            }
        time.sleep(delay)

    return list(results.values())
