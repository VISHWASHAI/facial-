import json
from utils.youtube_search import search_youtube, search_youtube_videos

# Load emotion-language search queries
with open("assets/playlists.json", "r") as f:
    playlists = json.load(f)

def get_music_url(emotion, language):
    query = playlists.get(emotion, {}).get(language)
    if not query:
        print(f"No playlist found for {emotion} in {language}. Using fallback.")
        return search_youtube(f"{emotion} songs in English")
    return search_youtube(query)

def get_therapeutic_music(emotion):
    therapeutic_queries = {
        "Sad": "Calming music for sadness",
        "Fearful": "Relaxing music for anxiety",
        "Angry": "Peaceful music for anger",
        "Bored": "Focus music for boredom",
        "Confused": "Grounding music for clarity",
        "Disgusted": "Soothing music for stress relief",
        "Excited": "Uplifting instrumental music",
        "Surprised": "Ambient music for reflection",
        "Neutral": "Chill background music",
        "Happy": "Feel-good acoustic tracks"
    }
    query = therapeutic_queries.get(emotion, "Calming music")
    return search_youtube(query)



# Target mood -> search queries. The first is the main recommendation; the rest are
# similar-mood variants used by "More Like This". Edit freely.
MOOD_QUERIES = {
    "Calm":      ["calm relaxing songs", "peaceful acoustic songs", "soft soothing melodies", "lofi chill beats"],
    "Feel-good": ["feel good songs", "uplifting positive songs", "feel good acoustic", "sunny day playlist"],
    "Happy":     ["happy songs", "cheerful hit songs", "happy upbeat pop", "good vibes playlist"],
    "Energetic": ["energetic songs", "workout motivation songs", "high energy dance songs", "pump up playlist"],
}


def get_mood_songs(mood, language="English", variant=0, limit=8):
    """Songs for a target mood. `variant` picks one of the mood's query variants."""
    queries = MOOD_QUERIES.get(mood, MOOD_QUERIES["Feel-good"])
    base = queries[variant % len(queries)]
    return search_youtube_videos(f"{base} {language}", limit=limit)
