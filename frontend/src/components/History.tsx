import { useCallback, useEffect, useState } from "react";
import { api, HistoryItem } from "../api";

export default function History({ sessionId }: { sessionId: string }) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [onlyThisSession, setOnlyThisSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await api.history(onlyThisSession ? sessionId : undefined);
      setItems(data.items);
      setSummary(data.summary);
      setError(null);
    } catch {
      setError("Could not load history.");
    }
  }, [onlyThisSession, sessionId]);

  useEffect(() => { refresh(); }, [refresh]);

  async function clear() {
    if (!confirm("Delete all saved emotion history?")) return;
    await api.clearHistory();
    refresh();
  }

  const max = Math.max(1, ...Object.values(summary));

  return (
    <section className="card">
      <h2>Emotion history</h2>
      <div className="row">
        <label className="check">
          <input type="checkbox" checked={onlyThisSession} onChange={(e) => setOnlyThisSession(e.target.checked)} />
          Only this session
        </label>
        <button className="secondary" onClick={clear} disabled={items.length === 0}>Clear history</button>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {items.length === 0 && !error ? (
        <p className="muted">No emotions recorded yet. Run a detection first.</p>
      ) : (
        <>
          <div className="bars" aria-label="Emotion counts">
            {Object.entries(summary).map(([emotion, n]) => (
              <div key={emotion} className="bar-row">
                <span>{emotion}</span>
                <div className="bar"><div style={{ width: `${(n / max) * 100}%` }} /></div>
                <span>{n}</span>
              </div>
            ))}
          </div>
          <table>
            <thead><tr><th>Time</th><th>Emotion</th><th>Confidence</th><th>Session</th></tr></thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>{i.detected_at}</td>
                  <td>{i.emotion}</td>
                  <td>{i.confidence !== null ? `${i.confidence}%` : "manual"}</td>
                  <td>{i.session_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
