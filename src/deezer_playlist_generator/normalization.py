"""String normalization helpers for track matching."""

import re
import unicodedata
from difflib import SequenceMatcher


def normalize(value: str) -> str:
    """Lowercase a string and strip everything except letters and digits.

    Accented characters are decomposed via Unicode NFD so combining marks can
    be removed (e.g. ``Björk`` → ``bjork``).
    """
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]", "", without_marks)


def similarity(first: str, second: str) -> float:
    """Return a 0–1 similarity score between two strings after normalization."""
    return SequenceMatcher(
        None,
        normalize(first),
        normalize(second),
    ).ratio()
