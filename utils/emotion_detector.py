import cv2
import numpy as np
from keras.models import load_model

emotion_model = load_model("models/emotion_model.h5")

# The CNN is trained with flow_from_directory (models/train_emotion_model.py), so its
# outputs follow the alphabetical folder order, not the old 10-label list.
TRAINED_LABELS = ['Angry', 'Disgusted', 'Fearful', 'Happy', 'Neutral', 'Sad', 'Surprised']
LEGACY_LABELS = [
    'Happy', 'Sad', 'Angry', 'Neutral', 'Surprised',
    'Fearful', 'Disgusted', 'Confused', 'Bored', 'Excited'
]
num_outputs = emotion_model.output_shape[-1]
emotion_labels = TRAINED_LABELS if num_outputs == len(TRAINED_LABELS) else LEGACY_LABELS

# Load face detectors (frontal default + alt2 as a second opinion)
face_detectors = [
    cv2.CascadeClassifier(cv2.data.haarcascades + name)
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml")
]
# Head tilts to try, in degrees (0 first so upright faces stay fast)
TILT_ANGLES = (0, -15, 15, -30, 30)


def preprocess_face(gray_face):
    """48x48 grayscale, scaled to 0-1, shaped (1, 48, 48, 1) for the CNN."""
    face = cv2.resize(gray_face, (48, 48))
    return face.reshape(1, 48, 48, 1).astype("float32") / 255.0


def _find_face(gray):
    """Return (face_roi, box) for the largest face, trying small head tilts.

    The ROI is cut from the de-tilted image; the box is mapped back to the original frame.
    """
    h, w = gray.shape
    center = (w / 2, h / 2)
    for angle in TILT_ANGLES:
        rot = cv2.getRotationMatrix2D(center, angle, 1.0)
        img = gray if angle == 0 else cv2.warpAffine(gray, rot, (w, h))
        det_img = cv2.equalizeHist(img)  # equalize for detection in dim light
        for detector in face_detectors:
            faces = detector.detectMultiScale(det_img, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
            if len(faces) == 0:
                continue
            x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            if angle == 0:
                box = (x, y, fw, fh)
            else:
                inv = cv2.invertAffineTransform(rot)
                cx, cy = inv @ np.array([x + fw / 2, y + fh / 2, 1.0])
                box = (int(cx - fw / 2), int(cy - fh / 2), fw, fh)
            return img[y:y+fh, x:x+fw], box
    return None, None


def analyze_frame(frame, bgr=True):
    """Detect the largest face in a frame and classify it.

    Returns (emotion, confidence, (x, y, w, h)) or ("No Face", 0, None).
    """
    code = cv2.COLOR_BGR2GRAY if bgr else cv2.COLOR_RGB2GRAY
    gray = cv2.cvtColor(frame, code)
    roi, box = _find_face(gray)
    if roi is None:
        return "No Face", 0, None

    prediction = emotion_model(preprocess_face(roi), training=False).numpy()[0]
    index = int(np.argmax(prediction))
    return emotion_labels[index], round(float(prediction[index]) * 100, 2), box


# Detect emotion from a single RGB frame (Streamlit camera_input / PIL)
def detect_emotion(frame):
    emotion, confidence, _ = analyze_frame(frame, bgr=False)
    return emotion, confidence
