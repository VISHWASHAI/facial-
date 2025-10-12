import cv2
import numpy as np
from keras.models import load_model

emotion_model = load_model("models/emotion_model.h5")

# Custom emotion labels (expanded)
emotion_labels = [
    'Happy', 'Sad', 'Angry', 'Neutral', 'Surprised',
    'Fearful', 'Disgusted', 'Confused', 'Bored', 'Excited'
]

# Load face detector
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Detect emotion from a frame
def detect_emotion(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        roi = gray[y:y+h, x:x+w]
        roi = cv2.resize(roi, (48, 48))
        roi = roi.reshape(1, 48, 48, 1).astype("float32") / 255.0
        prediction = emotion_model.predict(roi)[0]
        emotion_index = np.argmax(prediction)
        emotion = emotion_labels[emotion_index]
        confidence = round(prediction[emotion_index] * 100, 2)
        return emotion, confidence

    return "No Face", 0

