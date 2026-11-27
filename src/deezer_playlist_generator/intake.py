"""Interactive program intake for playlist preferences."""

from deezer_playlist_generator.models import PlaylistPreferences


class ProgramIntake:
    """Collect and validate user preferences from the terminal."""

    def collect(self) -> PlaylistPreferences:
        self._print_welcome()

        keywords = self._prompt_keywords()
        track_count = self._prompt_track_count()
        prefer_obscure = self._prompt_yes_no(
            "Would you like us to prefer obscure tracks? [y/N]: "
        )
        create_on_deezer = self._prompt_yes_no(
            "Would you like us to create a playlist on Deezer for you? [y/N]: "
        )

        print(
            f"Creating playlist with {track_count} tracks, "
            f"prefer_obscure={prefer_obscure}, "
            f"create_on_deezer={create_on_deezer}."
        )
        print("Sit back, relax, and let us build your playlist!")

        return PlaylistPreferences(
            keywords=keywords,
            track_count=track_count,
            prefer_obscure=prefer_obscure,
            create_on_deezer=create_on_deezer,
        )

    @staticmethod
    def _print_welcome() -> None:
        print("Welcome to the Deezer Playlist Creator!")
        print(
            "This script will curate a playlist for you, "
            "based on the keywords you provide."
        )
        print(
            "Keywords can be: artist names, song titles, moods, "
            "genres, years, etc."
        )
        print(
            "You can also specify if you want us to prefer "
            "obscure, non-mainstream tracks."
        )
        print(
            "Finally, you can specify if you want us to create "
            "a playlist on Deezer for you."
        )
        print("If not we will only show you the playlist in json format.")
        print("Let's get started!")

    @staticmethod
    def _prompt_keywords() -> list[str]:
        raw = input(
            "Please enter the keywords you want to use to search for tracks "
            "in a single string, separated by commas:"
        )
        return [keyword.strip() for keyword in raw.split(",") if keyword.strip()]

    @staticmethod
    def _prompt_track_count(minimum: int = 10, maximum: int = 40) -> int:
        while True:
            raw = input(
                f"Please enter the number of tracks you want to include "
                f"in the playlist, from {minimum} to {maximum}: "
            ).strip()
            try:
                track_count = int(raw)
            except ValueError:
                print(
                    f"Invalid number of tracks. Please enter a number "
                    f"between {minimum} and {maximum}."
                )
                continue

            if minimum <= track_count <= maximum:
                return track_count

            print(
                f"Invalid number of tracks. Please enter a number "
                f"between {minimum} and {maximum}."
            )

    @staticmethod
    def _prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
        answer = input(prompt).strip().lower()
        if not answer:
            return default
        return answer in {"y", "yes"}
