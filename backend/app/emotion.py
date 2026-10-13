"""Webcam frame -> face detection (OpenCV YuNet) -> emotion (HSEmotion EfficientNet, ONNX)."""
import threading
import urllib.request  # noqa: F401  (hsemotion_onnx uses urllib.request without importing it)
from pathlib import Path

import cv2
import numpy as np
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer

WEIGHTS = Path(__file__).parent / "weights" / "face_detection_yunet_2023mar.onnx"
EMOTION_MODEL = "enet_b0_8_best_vgaf"

# HSEmotion label -> label used by the rest of the app
LABELS = {
    "Anger": "Angry", "Contempt": "Contempt", "Disgust": "Disgusted", "Fear": "Fearful",
    "Happiness": "Happy", "Neutral": "Neutral", "Sadness": "Sad", "Surprise": "Surprised",
}
MAX_WIDTH = 640  # frames wider than this are downscaled before detection


class EmotionEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._detector = cv2.FaceDetectorYN.create(str(WEIGHTS), "", (320, 320), 0.7, 0.3, 5000)
        self._recognizer = None  # loaded on first face (downloads weights once)

    def _load_recognizer(self):
        if self._recognizer is None:
            self._recognizer = HSEmotionRecognizer(model_name=EMOTION_MODEL)
        return self._recognizer

    def classify_face(self, face_rgb):
        """Classify an already-cropped RGB face. Returns {label: probability}."""
        recognizer = self._load_recognizer()
        _, scores = recognizer.predict_emotions(face_rgb, logits=False)
        return {LABELS[recognizer.idx_to_class[i]]: float(s) for i, s in enumerate(scores)}

    def analyze(self, frame_bgr):
        """Find the largest face and classify it.

        Returns None if no face, else {emotion, confidence, box (x, y, w, h as 0-1 fractions), scores}.
        """
        h, w = frame_bgr.shape[:2]
        if w > MAX_WIDTH:
            frame_bgr = cv2.resize(frame_bgr, (MAX_WIDTH, int(h * MAX_WIDTH / w)))
            h, w = frame_bgr.shape[:2]

        with self._lock:
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(frame_bgr)
            if faces is None or len(faces) == 0:
                return None
            x, y, fw, fh = (float(v) for v in max(faces, key=lambda f: f[2] * f[3])[:4])

            # small margin around the face, clipped to the frame
            m = 0.1
            x0, y0 = max(int(x - m * fw), 0), max(int(y - m * fh), 0)
            x1, y1 = min(int(x + fw * (1 + m)), w), min(int(y + fh * (1 + m)), h)
            if x1 - x0 < 10 or y1 - y0 < 10:
                return None
            face = cv2.cvtColor(frame_bgr[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
            scores = self.classify_face(face)

        emotion = max(scores, key=scores.get)
        return {
            "emotion": emotion,
            "confidence": round(float(scores[emotion]) * 100, 1),
            "box": [round(max(x, 0) / w, 4), round(max(y, 0) / h, 4), round(fw / w, 4), round(fh / h, 4)],
            "scores": {k: round(float(v), 4) for k, v in scores.items()},
        }

    def analyze_jpeg(self, data: bytes):
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image")
        return self.analyze(frame)


_engine = None
_engine_lock = threading.Lock()


def get_engine() -> EmotionEngine:
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = EmotionEngine()
        return _engine
