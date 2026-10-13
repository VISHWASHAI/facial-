import { useEffect, useState } from "react";
import { api, Plan } from "./api";
import Detector from "./components/Detector";
import History from "./components/History";
import MusicPanel from "./components/MusicPanel";

interface Result {
  emotion: string;
  confidence: number | null;
  plan: Plan;
}

// one id per browser tab session, used to group saved emotions
function sessionId(): string {
  let id = sessionStorage.getItem("session_id");
  if (!id) {
    id = Math.random().toString(36).slice(2, 10);
    sessionStorage.setItem("session_id", id);
  }
  return id;
}

export default function App() {
  const [sid] = useState(sessionId);
  const [tab, setTab] = useState<"listen" | "history">("listen");
  const [moods, setMoods] = useState<string[]>([]);
  const [languages, setLanguages] = useState<string[]>(["English"]);
  const [language, setLanguage] = useState("English");
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.moods().then((m) => { setMoods(m.moods); setLanguages(m.languages); }).catch(() => {
      setError("Could not reach the backend. Start it with: uvicorn app.main:app (see README).");
    });
  }, []);

  async function handleResult(emotion: string, confidence: number | null) {
    setBusy(true);
    setError(null);
    try {
      // detected emotion -> SQLite -> rule-based mood plan
      const { plan } = await api.recordEmotion(sid, emotion, confidence);
      setResult({ emotion, confidence, plan });
    } catch {
      setError("Could not save the emotion. Is the backend running?");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>🎵 Emotion Music</h1>
        <p className="muted">Your face picks the mood. The mood picks the music.</p>
        <nav role="tablist">
          <button role="tab" aria-selected={tab === "listen"} onClick={() => setTab("listen")}>Detect &amp; listen</button>
          <button role="tab" aria-selected={tab === "history"} onClick={() => setTab("history")}>History</button>
        </nav>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      <main>
        {tab === "listen" ? (
          <>
            <label className="field">
              Music language
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                {languages.map((l) => <option key={l}>{l}</option>)}
              </select>
            </label>
            <Detector busy={busy} onResult={handleResult} />
            {result && <MusicPanel {...result} language={language} moods={moods} />}
          </>
        ) : (
          <History sessionId={sid} />
        )}
      </main>
    </div>
  );
}
