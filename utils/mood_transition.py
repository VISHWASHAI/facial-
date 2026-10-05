# Rule-based mood transition: detected emotion -> steps toward a better mood.
# The first step is the target mood used right now; later steps are where to go next.
# Edit this dictionary to change the behaviour.
MOOD_TRANSITIONS = {
    "Sad":       ["Calm", "Feel-good"],
    "Angry":     ["Calm", "Feel-good"],
    "Fearful":   ["Calm", "Feel-good"],
    "Disgusted": ["Calm", "Feel-good"],
    "Bored":     ["Energetic", "Feel-good"],
    "Confused":  ["Calm", "Feel-good"],
    "Neutral":   ["Feel-good"],
    "Surprised": ["Feel-good"],
    "Happy":     ["Happy", "Energetic"],
    "Excited":   ["Energetic", "Happy"],
}
DEFAULT_PATH = ["Feel-good"]

ALL_MOODS = ["Calm", "Feel-good", "Happy", "Energetic"]


def get_mood_path(emotion):
    return MOOD_TRANSITIONS.get(emotion, DEFAULT_PATH)


def get_target_mood(emotion):
    return get_mood_path(emotion)[0]
