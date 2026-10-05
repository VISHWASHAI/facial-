import time
from collections import Counter

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from utils.emotion_detector import analyze_frame, detect_emotion
from utils.emotion_db import new_session_id, save_emotion, get_history, clear_history
from utils.mood_transition import get_mood_path, ALL_MOODS
from utils.music_mapper import get_mood_songs

LANGUAGES = [
    'Tamil', 'Telugu', 'Malayalam', 'Kannada', 'Hindi', 'Bengali', 'Marathi',
    'Gujarati', 'Punjabi', 'Urdu', 'Russian', 'French', 'Spanish', 'German', 'English'
]
MANUAL_EMOTIONS = ["Happy", "Sad", "Angry", "Fearful", "Neutral", "Surprised", "Disgusted", "Bored"]

affirmations = {
    "Sad": "You are stronger than you feel right now.",
    "Fearful": "You are safe. You are capable.",
    "Angry": "Take a deep breath. You are in control.",
    "Bored": "Every moment is a chance to grow."
}

st.set_page_config(page_title="Emotion Detector", layout="centered")

# ---------- session state ----------
state = st.session_state
state.setdefault("session_id", new_session_id())
state.setdefault("emotion", None)
state.setdefault("mood_path", [])
state.setdefault("target_mood", None)
state.setdefault("variant", 0)
state.setdefault("songs", [])
state.setdefault("song_idx", 0)
state.setdefault("more_songs", [])


def load_songs(language):
    state.songs = get_mood_songs(state.target_mood, language, state.variant)
    state.song_idx = 0
    state.more_songs = []


def set_emotion(emotion, confidence, language):
    """Detected emotion -> SQLite -> mood transition -> first recommendation."""
    save_emotion(state.session_id, emotion, confidence)
    state.emotion = emotion
    state.mood_path = get_mood_path(emotion)
    state.target_mood = state.mood_path[0]
    state.variant = 0
    load_songs(language)


def live_scan(seconds, language):
    """Webcam -> OpenCV -> face detection -> CNN, then keep the dominant emotion."""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        st.error("Could not open the webcam.")
        return
    frame_box = st.empty()
    status = st.empty()
    votes, confs = Counter(), {}
    start = time.time()
    try:
        while time.time() - start < seconds:
            ok, frame = cap.read()
            if not ok:
                break
            emotion, conf, box = analyze_frame(frame, bgr=True)
            if box is not None:
                x, y, w, h = box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{emotion} {conf:.0f}%", (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                votes[emotion] += 1
                confs.setdefault(emotion, []).append(conf)
            frame_box.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB")
            status.caption(f"Scanning... {max(0, seconds - int(time.time() - start))}s left")
    finally:
        cap.release()
    frame_box.empty()
    status.empty()

    if not votes:
        st.warning("No face detected. Face the camera in good light and try again.")
        return
    emotion = votes.most_common(1)[0][0]
    set_emotion(emotion, round(float(np.mean(confs[emotion])), 2), language)


# ---------- UI ----------
st.title("🎵 Emotion-Based Music Recommender")
tab_music, tab_history = st.tabs(["🎧 Detect & Listen", "📜 Emotion History"])

with tab_music:
    mode = st.radio("🧭 Select Mode", ["Live Webcam", "Snapshot", "Manual"], horizontal=True)
    language = st.selectbox("🌐 Choose Your Language", LANGUAGES, index=LANGUAGES.index("English"))

    if mode == "Live Webcam":
        seconds = st.slider("Scan duration (seconds)", 3, 20, 6)
        if st.button("🎥 Start Live Detection"):
            live_scan(seconds, language)
    elif mode == "Snapshot":
        image_data = st.camera_input("📸 Capture your emotion")
        if image_data is not None and st.button("Analyze snapshot"):
            emotion, conf = detect_emotion(np.array(Image.open(image_data).convert("RGB")))
            if emotion == "No Face":
                st.warning("No face detected. Try again.")
            else:
                set_emotion(emotion, conf, language)
    else:
        picked = st.selectbox("🎭 Select Your Emotion", MANUAL_EMOTIONS)
        if st.button("Use this emotion"):
            set_emotion(picked, None, language)

    # ----- result + recommendation -----
    if state.emotion:
        st.divider()
        st.success(f"Detected Emotion: **{state.emotion}**")
        if state.emotion in affirmations:
            st.markdown(f"💬 *{affirmations[state.emotion]}*")
        st.info("Mood transition: " + " → ".join([state.emotion] + state.mood_path)
                + f"  |  Target mood now: **{state.target_mood}**")

        if state.songs:
            song = state.songs[state.song_idx % len(state.songs)]
            st.subheader(f"🎶 {state.target_mood} music")
            st.caption(song["title"])
            st.video(f"https://www.youtube.com/watch?v={song['id']}")
        else:
            st.warning("No songs found right now. Check your connection and try again.")

        c1, c2, c3 = st.columns(3)
        if c1.button("🔁 More Like This", use_container_width=True):
            # similar mood, different query variant
            state.variant += 1
            state.more_songs = get_mood_songs(state.target_mood, language, state.variant, limit=4)
        if c2.button("🎭 Change the Mood", use_container_width=True):
            state.choosing_mood = True
        if c3.button("⏭ Try Another Song", use_container_width=True) and state.songs:
            state.song_idx = (state.song_idx + 1) % len(state.songs)
            st.rerun()

        if state.get("choosing_mood"):
            idx = ALL_MOODS.index(state.target_mood) if state.target_mood in ALL_MOODS else 0
            new_mood = st.selectbox("Pick a target mood", ALL_MOODS, index=idx)
            if st.button("Play this mood"):
                state.target_mood = new_mood
                state.variant = 0
                state.choosing_mood = False
                load_songs(language)
                st.rerun()

        if state.more_songs:
            st.subheader("More like this")
            for s in state.more_songs:
                st.caption(s["title"])
                st.video(f"https://www.youtube.com/watch?v={s['id']}")

with tab_history:
    st.subheader("Your previous emotions")
    only_session = st.checkbox("Only this session", value=False)
    rows = get_history(state.session_id if only_session else None)
    if rows:
        df = pd.DataFrame(rows, columns=["Time", "Emotion", "Confidence (%)", "Session"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df["Emotion"].value_counts())
    else:
        st.write("No emotions recorded yet.")
    if st.button("🗑 Clear history"):
        clear_history()
        st.rerun()
