import streamlit as st
import numpy as np
from PIL import Image
from utils.emotion_detector import detect_emotion
from utils.music_mapper import get_music_url, get_therapeutic_music

# Affirmations for therapeutic emotions
affirmations = {
    "Sad": "You are stronger than you feel right now.",
    "Fearful": "You are safe. You are capable.",
    "Angry": "Take a deep breath. You are in control.",
    "Bored": "Every moment is a chance to grow."
}

therapeutic_emotions = list(affirmations.keys())

# Page setup
st.set_page_config(page_title="Emotion Detector", layout="centered")
st.title("🎵 Emotion-Based Music Recommender")
st.write("Choose a mode and let your emotion guide your music.")

# Mode selection
mode = st.radio("🧭 Select Mode", ["Automatic", "Manual"])

# Language selection
language = st.selectbox("🌐 Choose Your Language", [
    'Tamil', 'Telugu', 'Malayalam', 'Kannada', 'Hindi', 'Bengali', 'Marathi',
    'Gujarati', 'Punjabi', 'Urdu', 'Russian', 'French', 'Spanish', 'German', 'English'
])

# Automatic Mode
if mode == "Automatic":
    image_data = st.camera_input("📸 Smile and click to capture your emotion")

    if image_data is not None:
        st.image(image_data, caption="Captured Frame")

        # Convert to OpenCV format
        image = Image.open(image_data)
        frame = np.array(image)

        # Emotion detection
        emotion, confidence = detect_emotion(frame)
        st.success(f"Detected Emotion: {emotion} ({confidence}%)")

        # Therapeutic Mode
        if emotion in therapeutic_emotions:
            st.subheader("🧘 Therapeutic Mode Activated")
            st.markdown(f"💬 *{affirmations[emotion]}*")
            music_url = get_therapeutic_music(emotion)
            st.components.v1.iframe(music_url, height=400)

            if st.button("🧘 Start Guided Breathing"):
                st.video("https://www.youtube.com/embed/GBgKJd7r0XY")
        else:
            music_url = get_music_url(emotion, language)
            st.components.v1.iframe(music_url, height=400)

# Manual Mode
elif mode == "Manual":
    emotion = st.selectbox("🎭 Select Your Emotion", [
        "Happy", "Sad", "Angry", "Fearful", "Neutral", "Surprised", "Disgusted", "Bored"
    ])
    st.success(f"Selected Emotion: {emotion}")

    # Therapeutic Mode
    if emotion in therapeutic_emotions:
        st.subheader("🧘 Therapeutic Mode Activated")
        st.markdown(f"💬 *{affirmations[emotion]}*")
        music_url = get_therapeutic_music(emotion)
        st.components.v1.iframe(music_url, height=400)

        if st.button("🧘 Start Guided Breathing"):
            st.video("https://www.youtube.com/embed/GBgKJd7r0XY")
    else:
        music_url = get_music_url(emotion, language)
        st.components.v1.iframe(music_url, height=400)
