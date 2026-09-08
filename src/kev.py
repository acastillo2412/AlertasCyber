"""Catalogo CISA KEV (vulnerabilidades explotadas activamente), usado para
priorizar la recomendacion de actuar o no en los resumenes."""

import logging

import requests

log = logging.getLogger("alertacyber")

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def fetch_kev_ids() -> set[str]:
    try:
        resp = requests.get(KEV_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {v["cveID"] for v in data.get("vulnerabilities", []) if v.get("cveID")}
    except Exception:
        log.warning("No se pudo consultar el catalogo CISA KEV, se omite en el resumen", exc_info=True)
        return set()
