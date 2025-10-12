import streamlit as st

st.set_page_config(page_title="Facial Emotion Music Recommender", layout="centered")

# Hero Section
st.markdown("""
<style>
.big-title {
    font-size: 48px;
    font-weight: bold;
    text-align: center;
    margin-top: 40px;
}
.subtitle {
    font-size: 20px;
    text-align: center;
    color: #555;
}
.feature-box {
    background-color: #f9f9f9;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🎶 Emotion-Based Music Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Let your face choose your music. In 15 languages. In real time.</div>', unsafe_allow_html=True)

st.image("assets/hero_image.png", caption="Your mood. Your music.", use_container_width=True)


# Features Section
st.header("✨ Features")
features = [
    "🎭 Real-time emotion detection via webcam",
    "🌐 Music recommendations in 15 languages",
    "🧘 Therapeutic mode for stress and sadness",
    "🎵 Curated playlists based on your mood",
    "📱 Works on desktop and mobile browsers"
]
for f in features:
    st.markdown(f"- {f}")

# Call to Action
st.header("🚀 Get Started")
st.markdown("""
Ready to experience music that understands you?

👉 Click below to launch the app and start detecting your emotion.

""")
if st.button("🎬 Launch Emotion Detector"):
    st.page_link("pages/app.py", label="🎬 Launch Emotion Detector")


# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Chitra")
