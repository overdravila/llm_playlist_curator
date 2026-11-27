"""Orchestrate track resolution and optional Deezer playlist creation."""

from __future__ import annotations

import json

from deezer_playlist_generator import catalog
from deezer_playlist_generator.deezer_client import DeezerMcpClient
from deezer_playlist_generator.models import PlaylistPreferences, TrackRequest
from deezer_playlist_generator.track_resolver import TrackResolver


class PlaylistCreator:
    """Resolve catalog tracks, preview them, then create or dump the playlist."""

    def __init__(
        self,
        client: DeezerMcpClient,
        preferences: PlaylistPreferences,
        tracks: list[TrackRequest] | None = None,
        *,
        title: str = catalog.TITLE,
        description: str = catalog.DESCRIPTION,
    ) -> None:
        self._client = client
        self._preferences = preferences
        self._tracks = tracks if tracks is not None else list(catalog.TRACKS)
        self._title = title
        self._description = description
        self._resolver = TrackResolver(client)

    async def run(self) -> None:
        matches, unresolved = await self._resolve_all()

        print(f"\nMatched: {len(matches)}/{len(self._tracks)}")

        if unresolved:
            print("\nUnresolved tracks:")
            for request in unresolved:
                print(f"  - {request.artist} - {request.title}")

            print("\nNo playlist created. Resolve these matches first.")
            return

        self._print_preview(matches)

        playlist_payload = {
            "title": self._title,
            "description": self._description,
            "private": True,
            "collaborative": False,
            "track_ids": [str(track["id"]) for track in matches],
            "tracks": [
                {
                    "id": track["id"],
                    "artist": track.get("artist"),
                    "title": track.get("title"),
                    "duration": track.get("duration"),
                }
                for track in matches
            ],
        }

        if not self._preferences.create_on_deezer:
            print("\nPlaylist JSON (Deezer creation skipped):")
            print(json.dumps(playlist_payload, indent=2, ensure_ascii=False))
            return

        confirmation = (
            input("\nCreate this PRIVATE Deezer playlist? [y/N]: ").strip().lower()
        )
        if confirmation != "y":
            print("Cancelled. Nothing was created.")
            return

        created = await self._client.create_playlist(
            title=self._title,
            description=self._description,
            track_ids=[str(track["id"]) for track in matches],
            private=True,
            collaborative=False,
        )

        print("\nPlaylist creation response:")
        print(json.dumps(created, indent=2, ensure_ascii=False))

    async def _resolve_all(self) -> tuple[list[dict], list[TrackRequest]]:
        matches: list[dict] = []
        unresolved: list[TrackRequest] = []
        used_ids: set[str] = set()

        print(f"\nSearching Deezer for {len(self._tracks)} tracks...\n")

        for index, request in enumerate(self._tracks, 1):
            try:
                track = await self._resolver.resolve(request)
            except Exception as exc:  # noqa: BLE001 - keep resolving remaining tracks
                print(
                    f"[{index:02}] SEARCH ERROR: "
                    f"{request.artist} - {request.title}: {exc}"
                )
                unresolved.append(request)
                continue

            if track is None:
                print(f"[{index:02}] NOT FOUND: {request.artist} - {request.title}")
                unresolved.append(request)
                continue

            track_id = str(track["id"])
            if track_id in used_ids:
                print(f"[{index:02}] DUPLICATE: {request.artist} - {request.title}")
                unresolved.append(request)
                continue

            used_ids.add(track_id)
            matches.append(track)

            duration = int(track.get("duration") or 0)
            duration_text = (
                f"{duration // 60}:{duration % 60:02}"
                if duration
                else "unknown duration"
            )
            print(
                f"[{index:02}] OK: {track['artist']} - "
                f"{track['title']} ({duration_text})"
            )

        return matches, unresolved

    @staticmethod
    def _print_preview(matches: list[dict]) -> None:
        total_seconds = sum(int(track.get("duration") or 0) for track in matches)

        print("\nPlaylist preview:")
        for index, track in enumerate(matches, 1):
            print(
                f"{index:02}. {track['artist']} - "
                f"{track['title']} [ID: {track['id']}]"
            )

        print(
            f"\nTotal duration: {total_seconds // 3600}h "
            f"{(total_seconds % 3600) // 60}m"
        )
