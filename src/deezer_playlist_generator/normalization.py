"""String normalization helpers for track matching."""

import re
from difflib import SequenceMatcher


def normalize(value: str) -> str:
    """Lowercase a string and strip everything except letters and digits."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def similarity(first: str, second: str) -> float:
    """Return a 0–1 similarity score between two strings after normalization."""
    return SequenceMatcher(
        None,
        normalize(first),
        normalize(second),
    ).ratio()
