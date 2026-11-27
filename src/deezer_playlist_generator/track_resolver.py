"""Resolve artist/title pairs to Deezer track records."""

from __future__ import annotations

from deezer_playlist_generator.deezer_client import DeezerMcpClient
from deezer_playlist_generator.matching import get_fallback_queries, rank_candidates
from deezer_playlist_generator.models import TrackRequest


class TrackResolver:
    """Find the best Deezer match for each requested track."""

    def __init__(self, client: DeezerMcpClient) -> None:
        self._client = client

    async def resolve(self, request: TrackRequest) -> dict | None:
        """Find the best Deezer track for an artist/title, using fallbacks if needed.

        Tries a primary "artist title" search first. If nothing ranks confidently,
        runs alias-aware fallback queries and re-ranks the combined candidates.
        Returns the winning track dict, or None if no match clears the thresholds.
        """
        artist = request.artist
        title = request.title

        candidates = await self._client.search_tracks(f"{artist} {title}")
        ranked = rank_candidates(artist, title, candidates)

        if ranked:
            return ranked[0][1]

        print(f"\n  No confident match: {artist} - {title}")
        print("  Trying alternative searches...")

        all_candidates = list(candidates)
        seen_ids = {str(track.get("id")) for track in all_candidates}

        for query in get_fallback_queries(artist, title):
            fallback_candidates = await self._client.search_tracks(query)

            print(f"\n  Search: {query}")

            for track in fallback_candidates:
                track_id = str(track.get("id"))

                if track_id not in seen_ids:
                    all_candidates.append(track)
                    seen_ids.add(track_id)

                print(
                    f"    {track.get('artist')} - {track.get('title')} "
                    f"[ID: {track_id}]"
                )

        ranked = rank_candidates(artist, title, all_candidates)
        if ranked:
            return ranked[0][1]

        return None
