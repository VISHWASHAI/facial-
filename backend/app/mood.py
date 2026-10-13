"""Rule-based mood transition: detected emotion -> steps toward a better mood.

The first step is the target mood used right now; later steps are where to go next.
Edit MOOD_TRANSITIONS to change the behaviour (no ML involved).
"""
MOOD_TRANSITIONS = {
    "Sad":       ["Calm", "Feel-good"],
    "Angry":     ["Calm", "Feel-good"],
    "Fearful":   ["Calm", "Feel-good"],
    "Disgusted": ["Calm", "Feel-good"],
    "Contempt":  ["Calm", "Feel-good"],
    "Neutral":   ["Feel-good"],
    "Surprised": ["Feel-good"],
    "Happy":     ["Happy", "Energetic"],
}
DEFAULT_PATH = ["Feel-good"]
ALL_MOODS = ["Calm", "Feel-good", "Happy", "Energetic"]

AFFIRMATIONS = {
    "Sad": "You are stronger than you feel right now.",
    "Fearful": "You are safe. You are capable.",
    "Angry": "Take a deep breath. You are in control.",
    "Disgusted": "This moment will pass. Breathe.",
    "Contempt": "Take a breath. You are in control.",
}


def get_mood_path(emotion: str) -> list[str]:
    return MOOD_TRANSITIONS.get(emotion, DEFAULT_PATH)


def plan(emotion: str) -> dict:
    path = get_mood_path(emotion)
    return {
        "emotion": emotion,
        "path": path,
        "target": path[0],
        "affirmation": AFFIRMATIONS.get(emotion),
    }
