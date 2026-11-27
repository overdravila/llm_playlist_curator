"""Default playlist metadata and seed track list."""

from deezer_playlist_generator.models import TrackRequest

TITLE = "Overcast, 1994 — The Other Side of 90s"
DESCRIPTION = (
    "A journey through the melancholic, atmospheric side of 90s "
    "alternative pop-rock. Familiar voices and overlooked gems."
)

# Artist, track title. Counting Crows are explicitly excluded.
TRACKS = [
    TrackRequest("Lisa Loeb", "Stay"),
    TrackRequest("Duncan Sheik", "Barely Breathing"),
    TrackRequest("Toad the Wet Sprocket", "Something's Always Wrong"),
    TrackRequest("Gin Blossoms", "Found Out About You"),
    TrackRequest("The Sundays", "Here's Where the Story Ends"),
    TrackRequest("The Connells", "74-75"),
    TrackRequest("Duncan Sheik", "She Runs Away"),
    TrackRequest("Lisa Loeb", "Do You Sleep?"),
    TrackRequest("Toad the Wet Sprocket", "Walk on the Ocean"),
    TrackRequest("Gin Blossoms", "Until I Fall Away"),
    TrackRequest("The Ocean Blue", "Between Something and Nothing"),
    TrackRequest("Del Amitri", "Driving with the Brakes On"),
    TrackRequest("Better Than Ezra", "Desperately Wanting"),
    TrackRequest("The Innocence Mission", "Bright as Yellow"),
    TrackRequest("The Devlins", "World Outside"),
    TrackRequest("The Wallflowers", "6th Avenue Heartache"),
    TrackRequest("The Verve Pipe", "The Freshmen"),
    TrackRequest("K's Choice", "Not an Addict"),
    TrackRequest("Toad the Wet Sprocket", "Windmills"),
    TrackRequest("Duncan Sheik", "Home"),
    TrackRequest("Lisa Loeb", "Waiting for Wednesday"),
    TrackRequest("Gin Blossoms", "Allison Road"),
    TrackRequest("The Samples", "Did You Ever Look so Nice"),
    TrackRequest("Matthew Sweet", "We're the Same"),
    TrackRequest("The Sundays", "When I'm Thinking About You"),
    TrackRequest("Toad the Wet Sprocket", "All I Want"),
    TrackRequest("Cracker", "Low"),
    TrackRequest("Sixpence None the Richer", "The Waiting Room"),
    TrackRequest("The Nixons", "Sister"),
    TrackRequest("Gin Blossoms", "Hey Jealousy"),
    TrackRequest("The Ocean Blue", "Sublime"),
]

# Alternative artist credits and titles accepted for known catalog variations.
ALIASES: dict[tuple[str, str], dict[str, list[str]]] = {
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
