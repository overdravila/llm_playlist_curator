import asyncio
import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parents[1]

TITLE = "Overcast, 1994 — The Other Side of 90s"
DESCRIPTION = (
    "A journey through the melancholic, atmospheric side of 90s "
    "alternative pop-rock. Familiar voices and overlooked gems."
)

# Artist, track title. Counting Crows are explicitly excluded.
TRACKS = [
    ("Lisa Loeb", "Stay"),
    ("Duncan Sheik", "Barely Breathing"),
    ("Toad the Wet Sprocket", "Something's Always Wrong"),
    ("Gin Blossoms", "Found Out About You"),
    ("The Sundays", "Here's Where the Story Ends"),
    ("The Connells", "74-75"),
    ("Duncan Sheik", "She Runs Away"),
    ("Lisa Loeb", "Do You Sleep?"),
    ("Toad the Wet Sprocket", "Walk on the Ocean"),
    ("Gin Blossoms", "Until I Fall Away"),
    ("The Ocean Blue", "Between Something and Nothing"),
    ("Del Amitri", "Driving with the Brakes On"),
    ("Better Than Ezra", "Desperately Wanting"),
    ("The Innocence Mission", "Bright as Yellow"),
    ("The Devlins", "World Outside"),
    ("The Wallflowers", "6th Avenue Heartache"),
    ("The Verve Pipe", "The Freshmen"),
    ("K's Choice", "Not an Addict"),
    ("Toad the Wet Sprocket", "Windmills"),
    ("Duncan Sheik", "Home"),
    ("Lisa Loeb", "Waiting for Wednesday"),
    ("Gin Blossoms", "Allison Road"),
    ("The Samples", "Did You Ever Look so Nice"),
    ("Matthew Sweet", "We're the Same"),
    ("The Sundays", "When I'm Thinking About You"),
    ("Toad the Wet Sprocket", "All I Want"),
    ("Cracker", "Low"),
    ("Sixpence None the Richer", "The Waiting Room"),
    ("The Nixons", "Sister"),
    ("Gin Blossoms", "Hey Jealousy"),
    ("The Ocean Blue", "Sublime"),
]

# Alternative artist credits and titles accepted for known catalog variations.
ALIASES = {
    ("Lisa Loeb", "Stay"): {
        "artists": ["Lisa Loeb", "Lisa Loeb & Nine Stories"],
        "titles": ["Stay", "Stay (I Missed You)"],
    },
    ("Lisa Loeb", "Waiting for Wednesday"): {
        "artists": ["Lisa Loeb", "Lisa Loeb & Nine Stories"],
        "titles": ["Waiting for Wednesday"],
    },
    ("The Rembrandts", "Drowning in Your Blue"): {
        "artists": ["The Rembrandts"],
        "titles": ["Drowning in Your Blue"],
    },
}


def normalize(value):
    """Lowercase a string and strip everything except letters and digits."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def similarity(first, second):
    """Return a 0–1 similarity score between two strings after normalization."""
    return SequenceMatcher(
        None,
        normalize(first),
        normalize(second),
    ).ratio()


def payload(result):
    """Extract the JSON body from an MCP tool result."""
    structured = getattr(
        result,
        "structuredContent",
        getattr(result, "structured_content", None),
    )

    if structured is not None:
        return structured

    for item in result.content:
        if hasattr(item, "text"):
            return json.loads(item.text)

    raise RuntimeError("Could not read the Deezer response.")


def get_fallback_queries(artist, title):
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


def rank_candidates(artist, title, candidates):
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

    ranked = []

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


async def search_tracks(session, query):
    """Search Deezer for tracks matching query; return the item list."""
    result = await session.call_tool(
        "search",
        {
            "query": query,
            "kind": "track",
            "limit": 10,
        },
    )

    if result.is_error:
        raise RuntimeError(f"Deezer search failed: {query}")

    data = payload(result)
    return data.get("tracks", {}).get("items", [])


async def resolve_track(session, artist, title):
    """Find the best Deezer track for an artist/title, using fallbacks if needed.

    Tries a primary \"artist title\" search first. If nothing ranks confidently,
    runs alias-aware fallback queries and re-ranks the combined candidates.
    Returns the winning track dict, or None if no match clears the thresholds.
    """
    candidates = await search_tracks(
        session,
        f"{artist} {title}",
    )

    ranked = rank_candidates(artist, title, candidates)

    if ranked:
        return ranked[0][1]

    print(f"\n  No confident match: {artist} - {title}")
    print("  Trying alternative searches...")

    all_candidates = list(candidates)
    seen_ids = {str(track.get("id")) for track in all_candidates}

    for query in get_fallback_queries(artist, title):
        fallback_candidates = await search_tracks(session, query)

        print(f"\n  Search: {query}")

        for track in fallback_candidates:
            track_id = str(track.get("id"))

            if track_id not in seen_ids:
                all_candidates.append(track)
                seen_ids.add(track_id)

            print(f"    {track.get('artist')} - {track.get('title')} [ID: {track_id}]")

    ranked = rank_candidates(artist, title, all_candidates)

    if ranked:
        return ranked[0][1]

    return None


async def main():
    """Resolve TRACKS on Deezer, preview matches, then create a private playlist."""
    env = os.environ.copy()
    env["DEEZER_ARL_FILE"] = str(Path.home() / ".config" / "deezer" / "arl")
    env["DEEZER_READ_ONLY"] = "0"
    env.pop("DEEZER_ARL", None)

    print("Welcome to the Deezer Playlist Creator!")
    print("This script will curate a playlist for you, based on the keywords you provide.")
    print("Keywords can be: artist names, song titles, moods, genres, years, etc.")
    print("You can also specify if you want us to prefer obscure, non-mainstream tracks.")
    print("Finally, you can specify if you want us to create a playlist on Deezer for you.")
    print("If not we will only show you the playlist in json format.")
    print("Let's get started!")
    
    keywords = (
        input("Please enter the keywords you want to use to search for tracks in a single string, separated by commas:")
        .strip()
        .split(",")
    )
    
    playlist_tracks = 0
    while playlist_tracks < 10 or playlist_tracks > 40:
        playlist_tracks = int(input("Please enter the number of tracks you want to include in the playlist, from 10 to 40: "))
        if playlist_tracks < 10 or playlist_tracks > 40:
            print("Invalid number of tracks. Please enter a number between 10 and 40.")
            continue
        break

    obscure_tracks = int(input("Would you like us to prefer obscure tracks? [y/N]: "))
    if obscure_tracks == "y":
        obscure_tracks = True
    else:
        obscure_tracks = False

    create_playlist_on_deezer = int(input("Would you like us to create a playlist on Deezer for you? [y/N]: "))
    if create_playlist_on_deezer == "y":
        create_playlist_on_deezer = True
    else:
        create_playlist_on_deezer = False

    print(f"Creating playlist with {playlist_tracks} tracks, {obscure_tracks} obscure tracks, and {create_playlist_on_deezer} create playlist on Deezer.")
    print("Sit back, relax, and let us build your playlist!")

    """This builds the MCP server through a uv command. The final command reads "uv run --project <PATH> mcp-deezer
        where --project flags that we are building a project from a PATH and mcp-deezer is the name of the package we are running."""
    server = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--project",
            str(PROJECT),
            "mcp-deezer",
        ],
        env=env,
    ) 

    async with (
        stdio_client(server) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        matches = []
        unresolved = []
        used_ids = set()

        print(f"\nSearching Deezer for {len(TRACKS)} tracks...\n")

        for index, (artist, title) in enumerate(TRACKS, 1):
            try:
                track = await resolve_track(
                    session,
                    artist,
                    title,
                )
            except Exception as exc:
                print(f"[{index:02}] SEARCH ERROR: {artist} - {title}: {exc}")
                unresolved.append((artist, title))
                continue

            if track is None:
                print(f"[{index:02}] NOT FOUND: {artist} - {title}")
                unresolved.append((artist, title))
                continue

            track_id = str(track["id"])

            if track_id in used_ids:
                print(f"[{index:02}] DUPLICATE: {artist} - {title}")
                unresolved.append((artist, title))
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

        print(f"\nMatched: {len(matches)}/{len(TRACKS)}")

        if unresolved:
            print("\nUnresolved tracks:")
            for artist, title in unresolved:
                print(f"  - {artist} - {title}")

            print("\nNo playlist created. Resolve these matches first.")
            return

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

        confirmation = (
            input("\nCreate this PRIVATE Deezer playlist? [y/N]: ").strip().lower()
        )

        if confirmation != "y":
            print("Cancelled. Nothing was created.")
            return

        result = await session.call_tool(
            "create_playlist",
            {
                "title": TITLE,
                "description": DESCRIPTION,
                "private": True,
                "collaborative": False,
                "track_ids": [str(track["id"]) for track in matches],
            },
        )

        if result.is_error:
            raise RuntimeError("Deezer playlist creation failed.")

        created = payload(result)

        print("\nPlaylist creation response:")
        print(json.dumps(created, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
