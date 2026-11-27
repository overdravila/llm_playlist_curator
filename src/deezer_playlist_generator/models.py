"""Shared data models for playlist generation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaylistPreferences:
    """User choices collected at program start."""

    keywords: list[str]
    track_count: int
    prefer_obscure: bool
    create_on_deezer: bool


@dataclass(frozen=True)
class TrackRequest:
    """An artist/title pair to resolve on Deezer."""

    artist: str
    title: str
