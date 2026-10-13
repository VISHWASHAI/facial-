import os
import tempfile

import cv2
import numpy as np
from fastapi.testclient import TestClient

os.environ["EMOTION_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from app import db, mood, music  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_mood_rules():
    assert mood.plan("Sad")["path"] == ["Calm", "Feel-good"]
    assert mood.plan("Sad")["target"] == "Calm"
    assert mood.plan("Neutral")["target"] == "Feel-good"
    assert mood.plan("Happy")["path"] == ["Happy", "Energetic"]
    assert mood.plan("SomethingNew")["target"] == "Feel-good"  # default rule


def test_history_roundtrip():
    db.clear_history()
    db.save_emotion("s1", "Sad", 80.0)
    db.save_emotion("s2", "Happy", 90.0)
    assert [r["emotion"] for r in db.get_history("s1")] == ["Sad"]
    assert db.get_history()[0]["emotion"] == "Happy"  # newest first
    assert db.get_summary() == {"Happy": 1, "Sad": 1}


def test_api_record_and_history():
    db.clear_history()
    r = client.post("/api/emotions", json={"session_id": "abc", "emotion": "Angry", "confidence": 71.5})
    assert r.status_code == 200
    assert r.json()["plan"]["target"] == "Calm"
    h = client.get("/api/history", params={"session_id": "abc"}).json()
    assert h["items"][0]["emotion"] == "Angry" and h["summary"] == {"Angry": 1}
    assert client.post("/api/emotions", json={"session_id": "", "emotion": "Sad"}).status_code == 422
    assert client.delete("/api/history").json() == {"cleared": True}
    assert client.get("/api/history").json()["items"] == []


def test_music_endpoint_uses_mood_queries(monkeypatch):
    seen = []
    monkeypatch.setattr(music, "_search", lambda q, n: (seen.append(q) or (("id1", "Song", "Ch"),)))
    r = client.get("/api/music", params={"mood": "Calm", "language": "Tamil", "variant": 1})
    assert r.json()["songs"] == [{"id": "id1", "title": "Song", "channel": "Ch"}]
    assert seen == ["peaceful acoustic songs Tamil"]
    assert client.get("/api/music", params={"mood": "Nope"}).status_code == 404


def test_analyze_no_face_and_bad_image():
    blank = cv2.imencode(".jpg", np.zeros((240, 320, 3), np.uint8))[1].tobytes()
    r = client.post("/api/analyze", files={"image": ("f.jpg", blank, "image/jpeg")})
    assert r.status_code == 200 and r.json() == {"face": None}
    bad = client.post("/api/analyze", files={"image": ("f.jpg", b"not an image", "image/jpeg")})
    assert bad.status_code == 400


def test_face_result_is_json_serializable(monkeypatch):
    """YuNet returns float32 arrays; the result must still be plain JSON types."""
    from app.emotion import EmotionEngine

    engine = EmotionEngine()
    face = np.array([[100, 80, 120, 140] + [0] * 11], dtype=np.float32)
    engine._detector = type("D", (), {"setInputSize": lambda s, size: None,
                                       "detect": lambda s, frame: (1, face)})()
    monkeypatch.setattr(engine, "classify_face", lambda img: {"Happy": np.float32(0.8), "Sad": np.float32(0.2)})
    result = engine.analyze(np.zeros((360, 480, 3), np.uint8))
    import json
    json.dumps(result)  # raises if numpy types leaked through
    assert result["emotion"] == "Happy" and result["confidence"] == 80.0
    assert all(0 <= v <= 1 for v in result["box"])


def test_websocket_frame():
    blank = cv2.imencode(".jpg", np.zeros((240, 320, 3), np.uint8))[1].tobytes()
    with client.websocket_connect("/ws/analyze") as ws:
        ws.send_bytes(blank)
        assert ws.receive_json() == {"face": None}
