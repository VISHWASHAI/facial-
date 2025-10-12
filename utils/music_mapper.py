import json
from utils.youtube_search import search_youtube

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

