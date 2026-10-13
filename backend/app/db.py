"""SQLite emotion history."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def _db_path() -> str:
    return os.environ.get("EMOTION_DB", str(Path(__file__).parent.parent / "emotion_history.db"))


@contextmanager
def connect():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emotion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            emotion TEXT NOT NULL,
            confidence REAL,
            detected_at TEXT NOT NULL
        )
    """)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def save_emotion(session_id: str, emotion: str, confidence: float | None = None) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO emotion_history (session_id, emotion, confidence, detected_at) VALUES (?, ?, ?, ?)",
            (session_id, emotion, confidence, now),
        )
    return {"id": cur.lastrowid, "session_id": session_id, "emotion": emotion,
            "confidence": confidence, "detected_at": now}


def get_history(session_id: str | None = None, limit: int = 200) -> list[dict]:
    query, params = "SELECT * FROM emotion_history", []
    if session_id:
        query += " WHERE session_id = ?"
        params.append(session_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return [dict(r) for r in conn.execute(query, params)]


def get_summary(session_id: str | None = None) -> dict:
    query, params = "SELECT emotion, COUNT(*) AS n FROM emotion_history", []
    if session_id:
        query += " WHERE session_id = ?"
        params.append(session_id)
    query += " GROUP BY emotion ORDER BY n DESC"
    with connect() as conn:
        return {r["emotion"]: r["n"] for r in conn.execute(query, params)}


def clear_history() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM emotion_history")
