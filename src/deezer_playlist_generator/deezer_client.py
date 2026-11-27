"""Deezer access through the mcp-deezer MCP server."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from start (or this file) until pyproject.toml is found."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    raise RuntimeError("Could not locate project root (missing pyproject.toml).")


def extract_payload(result: Any) -> Any:
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


class DeezerMcpClient:
    """Thin wrapper around an mcp-deezer ClientSession."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    @classmethod
    @asynccontextmanager
    async def connect(
        cls,
        project_root: Path | None = None,
    ) -> AsyncIterator[DeezerMcpClient]:
        """Start mcp-deezer over stdio and yield a ready client."""
        root = project_root or find_project_root()
        env = os.environ.copy()
        env["DEEZER_ARL_FILE"] = str(Path.home() / ".config" / "deezer" / "arl")
        env["DEEZER_READ_ONLY"] = "0"
        env.pop("DEEZER_ARL", None)

        # uv run --project <PATH> mcp-deezer
        server = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "--project",
                str(root),
                "mcp-deezer",
            ],
            env=env,
        )

        async with (
            stdio_client(server) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            yield cls(session)

    async def search_tracks(self, query: str, *, limit: int = 10) -> list[dict]:
        """Search Deezer for tracks matching query; return the item list."""
        result = await self._session.call_tool(
            "search",
            {
                "query": query,
                "kind": "track",
                "limit": limit,
            },
        )

        if result.is_error:
            raise RuntimeError(f"Deezer search failed: {query}")

        data = extract_payload(result)
        return data.get("tracks", {}).get("items", [])

    async def create_playlist(
        self,
        *,
        title: str,
        description: str,
        track_ids: list[str],
        private: bool = True,
        collaborative: bool = False,
    ) -> Any:
        """Create a Deezer playlist with the given tracks."""
        result = await self._session.call_tool(
            "create_playlist",
            {
                "title": title,
                "description": description,
                "private": private,
                "collaborative": collaborative,
                "track_ids": track_ids,
            },
        )

        if result.is_error:
            raise RuntimeError("Deezer playlist creation failed.")

        return extract_payload(result)
