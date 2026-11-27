"""CLI entrypoint for building a Deezer playlist."""

from __future__ import annotations

import asyncio

from deezer_playlist_generator.deezer_client import DeezerMcpClient
from deezer_playlist_generator.intake import ProgramIntake
from deezer_playlist_generator.playlist_creator import PlaylistCreator


async def async_main() -> None:
    preferences = ProgramIntake().collect()

    async with DeezerMcpClient.connect() as client:
        await PlaylistCreator(client, preferences).run()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
