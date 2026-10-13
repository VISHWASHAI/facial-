# Emotion Music (v2)

Your face picks the mood, the mood picks the music.

```
Webcam â†’ face detection â†’ emotion model â†’ SQLite history â†’ mood rule â†’ music â†’ More like this / Change the mood / Try another song
```

| Part | Technology |
|---|---|
| Backend API | Python, FastAPI, WebSocket for the real-time loop |
| Face detection | OpenCV YuNet (ONNX) |
| Emotion model | HSEmotion EfficientNet-B0 (ONNX, pretrained on AffectNet) |
| History | SQLite |
| Mood transition | Plain Python rules in `backend/app/mood.py` (no ML) |
| Music | YouTube search via `yt-dlp` (no API key), played with the YouTube embed |
| Frontend | React + TypeScript + Vite |

The previous Streamlit/Keras version is kept in git history under the tag `v1-streamlit`.

## Run it

Needs Python 3.10+ and Node 20+.

```powershell
# once
py -3.10 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend; npm install; npm run build; cd ..

# every time
.\start.ps1
```

Open http://localhost:8000. The first detection downloads the emotion model (15 MB, saved to ~/.hsemotion) once.

For frontend development run the API (`uvicorn app.main:app --reload` in `backend/`) and `npm run dev` in `frontend/`; Vite proxies `/api` and `/ws` to port 8000.

## How it works

1. **Detect & listen** â†’ *Start live detection* opens the webcam in the browser. Each frame goes over a WebSocket to the backend, which finds the face and classifies it. The most frequent emotion over the scan (3â€“15 s) is used, which smooths out frame-to-frame noise.
2. The emotion is saved to SQLite (`backend/emotion_history.db`: emotion, confidence, time, session) and the mood rules pick a target mood, e.g. `Sad â†’ Calm â†’ Feel-good`.
3. Songs for the target mood are shown with three buttons: **More like this** (similar query for the same mood), **Change the mood** (pick any mood) and **Try another song**.
4. **History** lists past emotions with counts and can be filtered to the current session.

To change the rules edit `MOOD_TRANSITIONS` in `backend/app/mood.py`; to change the music edit `MOOD_QUERIES` in `backend/app/music.py`.

## Tests and evaluation

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe evaluate.py --per-class 100   # needs the FER2013 images in data/
```

`evaluate.py` writes metric pictures to `docs/v2-evaluation/`. On a 700-image FER2013 sample the model scores **53.3 %** (7 emotions) and **74.6 %** (3 mood groups: negative / neutral / positive). The old v1 CNN scored 52.4 % / 73.6 % on the same images (`docs/v1-evaluation/`), so there is no big accuracy jump on this dataset: FER2013 is 48Ã—48 grayscale, a hard test for a model trained on color photos, and v1 was trained on FER2013 itself. Real webcam accuracy is not measured. Confidence is often below 60 %, so treat single readings as a hint, not a diagnosis.

## Notes

- The webcam needs `localhost` or HTTPS (browser rule).
- This is a music mood helper, not a medical or mental-health tool.
- `data/` (FER2013 images) is git-ignored; it is only needed for `evaluate.py`.
