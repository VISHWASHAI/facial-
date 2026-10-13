import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db, mood, music
from app.emotion import get_engine

app = FastAPI(title="Emotion Music API")

DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


class EmotionIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    emotion: str = Field(min_length=1, max_length=32)
    confidence: float | None = Field(default=None, ge=0, le=100)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(image: UploadFile = File(...)):
    """Analyze one JPEG/PNG frame. `face` is null when no face is found."""
    try:
        result = await run_in_threadpool(get_engine().analyze_jpeg, await image.read())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"face": result}


@app.websocket("/ws/analyze")
async def analyze_stream(ws: WebSocket):
    """Real-time loop: client sends a JPEG frame (binary), server replies with the result."""
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()
            try:
                result = await run_in_threadpool(get_engine().analyze_jpeg, data)
                await ws.send_json({"face": result})
            except Exception:  # one bad frame must not end the live session
                await ws.send_json({"face": None, "error": "bad frame"})
    except WebSocketDisconnect:
        pass


@app.post("/api/emotions")
def record_emotion(body: EmotionIn):
    """Save a detected emotion to SQLite and return the mood plan for it."""
    saved = db.save_emotion(body.session_id, body.emotion, body.confidence)
    return {"saved": saved, "plan": mood.plan(body.emotion)}


@app.get("/api/mood/{emotion}")
def mood_plan(emotion: str):
    return mood.plan(emotion)


@app.get("/api/moods")
def moods():
    return {"moods": mood.ALL_MOODS, "languages": music.LANGUAGES}


@app.get("/api/music")
async def songs(mood_name: str = Query(alias="mood"), language: str = "English",
                variant: int = Query(0, ge=0), limit: int = Query(8, ge=1, le=20)):
    if mood_name not in music.MOOD_QUERIES:
        raise HTTPException(404, f"Unknown mood '{mood_name}'")
    return {"mood": mood_name, "variant": variant,
            "songs": await run_in_threadpool(music.get_songs, mood_name, language, variant, limit)}


@app.get("/api/history")
def history(session_id: str | None = None, limit: int = Query(200, ge=1, le=1000)):
    return {"items": db.get_history(session_id, limit), "summary": db.get_summary(session_id)}


@app.delete("/api/history")
def delete_history():
    db.clear_history()
    return {"cleared": True}


@app.get("/api/session")
def new_session():
    return {"session_id": uuid.uuid4().hex[:8]}


# Serve the built frontend (npm run build) from the same server, if present
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        file = DIST / path
        return FileResponse(file if path and file.is_file() else DIST / "index.html")
