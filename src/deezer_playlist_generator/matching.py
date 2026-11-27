"""Rank Deezer search hits against expected artist/title pairs."""

from deezer_playlist_generator.catalog import ALIASES
from deezer_playlist_generator.normalization import similarity


def get_fallback_queries(artist: str, title: str) -> list[str]:
    """Return alternate search strings for tracks with known catalog quirks."""
    if (artist, title) == ("Lisa Loeb", "Stay"):
        return [
            "Stay (I Missed You)",
            "Lisa Loeb & Nine Stories Stay",
        ]

    if (artist, title) == ("Lisa Loeb", "Waiting for Wednesday"):
        return [
            "Waiting for Wednesday",
            "Lisa Loeb & Nine Stories",
        ]

    if (artist, title) == ("The Rembrandts", "Drowning in Your Blue"):
        return [
            "Drowning in Your Blue",
            "The Rembrandts",
        ]

    return [f"{artist} {title}"]


def rank_candidates(
    artist: str,
    title: str,
    candidates: list[dict],
) -> list[tuple[float, dict]]:
    """Score Deezer search hits against the expected artist/title (and aliases).

    Keeps only candidates that clear title and artist similarity thresholds,
    then returns them sorted best-first as (score, track) pairs.
    """
    aliases = ALIASES.get(
        (artist, title),
        {
            "artists": [artist],
            "titles": [title],
        },
    )

    ranked: list[tuple[float, dict]] = []

    for track in candidates:
        candidate_artist = track.get("artist") or ""
        candidate_title = track.get("title") or ""
        track_id = str(track.get("id", ""))

        if not track_id:
            continue

        title_score = max(
            similarity(expected, candidate_title) for expected in aliases["titles"]
        )
        artist_score = max(
            similarity(expected, candidate_artist) for expected in aliases["artists"]
        )
        score = (title_score * 0.65) + (artist_score * 0.35)

        if title_score >= 0.78 and artist_score >= 0.70:
            ranked.append((score, track))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked
