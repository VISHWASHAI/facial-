import sqlite3
import uuid
from datetime import datetime

DB_PATH = "emotion_history.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emotion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            emotion TEXT NOT NULL,
            confidence REAL,
            detected_at TEXT NOT NULL
        )
    """)
    return conn


def new_session_id():
    return uuid.uuid4().hex[:8]


def save_emotion(session_id, emotion, confidence=None):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO emotion_history (session_id, emotion, confidence, detected_at) VALUES (?, ?, ?, ?)",
            (session_id, emotion, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def get_history(session_id=None, limit=200):
    """Most recent first. Pass session_id to restrict to one session."""
    query = "SELECT detected_at, emotion, confidence, session_id FROM emotion_history"
    params = []
    if session_id:
        query += " WHERE session_id = ?"
        params.append(session_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    conn = _connect()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def clear_history():
    with _connect() as conn:
        conn.execute("DELETE FROM emotion_history")
