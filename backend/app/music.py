"""Mood -> YouTube search queries -> songs (via yt-dlp search, no API key needed)."""
from functools import lru_cache

from yt_dlp import YoutubeDL

LANGUAGES = [
    "English", "Tamil", "Telugu", "Malayalam", "Kannada", "Hindi", "Bengali", "Marathi",
    "Gujarati", "Punjabi", "Urdu", "Russian", "French", "Spanish", "German",
]

# Target mood -> search queries. The first is the main recommendation; the rest are
# similar-mood variants used by "More Like This". Edit freely.
MOOD_QUERIES = {
    "Calm":      ["calm relaxing songs", "peaceful acoustic songs", "soft soothing melodies", "lofi chill beats"],
    "Feel-good": ["feel good songs", "uplifting positive songs", "feel good acoustic", "sunny day playlist"],
    "Happy":     ["happy songs", "cheerful hit songs", "happy upbeat pop", "good vibes playlist"],
    "Energetic": ["energetic songs", "workout motivation songs", "high energy dance songs", "pump up playlist"],
}


@lru_cache(maxsize=256)
def _search(query: str, limit: int) -> tuple:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    try:
        with YoutubeDL(opts) as ydl:
            entries = ydl.extract_info(f"ytsearch{limit}:{query}", download=False).get("entries", [])
    except Exception:
        return ()
    return tuple(
        (e["id"], e.get("title") or "Untitled", e.get("channel") or e.get("uploader") or "")
        for e in entries if e and e.get("id")
    )


def get_songs(mood: str, language: str = "English", variant: int = 0, limit: int = 8) -> list[dict]:
    queries = MOOD_QUERIES.get(mood, MOOD_QUERIES["Feel-good"])
    query = f"{queries[variant % len(queries)]} {language}"
    return [{"id": i, "title": t, "channel": c} for i, t, c in _search(query, limit)]
