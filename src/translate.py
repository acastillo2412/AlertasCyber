"""Traduccion de descripciones de ingles a espanol via la API gratuita MyMemory."""

import logging

import requests

log = logging.getLogger("alertacyber")

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MAX_CHARS = 480  # limite practico por peticion en el nivel gratuito de MyMemory


def to_spanish(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return text

    try:
        resp = requests.get(
            MYMEMORY_URL,
            params={"q": text[:MAX_CHARS], "langpair": "en|es"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("responseStatus") == 200:
            translated = data.get("responseData", {}).get("translatedText", "").strip()
            if translated:
                return translated
    except Exception:
        log.warning("Fallo la traduccion, se usa el texto original en ingles", exc_info=True)

    return text
