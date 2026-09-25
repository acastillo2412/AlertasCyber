"""Comprobacion local de keywords por palabra completa.

La busqueda de NVD (keywordSearch) encuentra subcadenas: "unifi" coincide con
"unified" (p. ej. "Wazuh ... providing unified XDR") y "windows server" con
cualquier texto que contenga "windows" y "server" por separado. Aqui se exige
que cada palabra de la keyword aparezca como palabra completa.
"""

import re


def _word_pattern(word: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])")


def matches_any(keywords: list[str], text: str) -> bool:
    """True si alguna keyword tiene todas sus palabras como palabras completas en text."""
    haystack = (text or "").lower().replace("_", " ")
    for keyword in keywords:
        words = keyword.lower().split()
        if words and all(_word_pattern(w).search(haystack) for w in words):
            return True
    return False
