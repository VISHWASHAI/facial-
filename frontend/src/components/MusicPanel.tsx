import { useCallback, useEffect, useState } from "react";
import { api, Plan, Song } from "../api";

interface Props {
  emotion: string;
  confidence: number | null;
  plan: Plan;
  language: string;
  moods: string[];
}

export default function MusicPanel({ emotion, confidence, plan, language, moods }: Props) {
  const [mood, setMood] = useState(plan.target);
  const [variant, setVariant] = useState(0);
  const [songs, setSongs] = useState<Song[]>([]);
  const [index, setIndex] = useState(0);
  const [more, setMore] = useState<Song[]>([]);
  const [choosing, setChoosing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (m: string, v: number, limit: number) => {
    setLoading(true);
    setError(null);
    try {
      return (await api.songs(m, language, v, limit)).songs;
    } catch {
      setError("Could not load songs. Check your connection and try again.");
      return [];
    } finally {
      setLoading(false);
    }
  }, [language]);

  // a new detection (or language change) starts again from the plan's target mood
  useEffect(() => {
    let cancelled = false;
    setMood(plan.target);
    setVariant(0);
    setIndex(0);
    setMore([]);
    setChoosing(false);
    load(plan.target, 0, 8).then((s) => !cancelled && setSongs(s));
    return () => { cancelled = true; };
  }, [plan, load]);

  const current = songs[index % Math.max(songs.length, 1)];

  async function moreLikeThis() {
    const next = variant + 1;
    setVariant(next);
    setMore(await load(mood, next, 4));
  }

  async function changeMood(m: string) {
    setMood(m);
    setVariant(0);
    setIndex(0);
    setMore([]);
    setChoosing(false);
    setSongs(await load(m, 0, 8));
  }

  function play(song: Song) {
    setSongs((s) => [song, ...s.filter((x) => x.id !== song.id)]);
    setIndex(0);
  }

  return (
    <section className="card">
      <h2>You look <strong>{emotion}</strong>{confidence !== null && <span className="muted"> ({confidence}%)</span>}</h2>
      {plan.affirmation && <p className="affirmation">“{plan.affirmation}”</p>}
      <p className="path" aria-label="Mood transition">
        {[emotion, ...plan.path].map((step, i, all) => (
          <span key={i}>
            <span className={`pill ${i === 1 ? "target" : ""}`}>{step}</span>
            {i < all.length - 1 && " → "}
          </span>
        ))}
      </p>

      <h3>🎶 {mood} music</h3>
      {current ? (
        <>
          <div className="player">
            <iframe
              key={current.id}
              src={`https://www.youtube.com/embed/${current.id}?autoplay=1`}
              title={current.title}
              allow="autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          </div>
          <p className="song-title">{current.title}</p>
        </>
      ) : (
        <p className="muted">{loading ? "Finding songs…" : error ?? "No songs found."}</p>
      )}

      <div className="actions">
        <button onClick={moreLikeThis} disabled={loading || !current}>More like this</button>
        <button onClick={() => setChoosing((c) => !c)} className="secondary">Change the mood</button>
        <button onClick={() => setIndex((i) => (i + 1) % songs.length)} disabled={songs.length < 2}>Try another song</button>
      </div>

      {choosing && (
        <div className="chips" role="group" aria-label="Pick a target mood">
          {moods.map((m) => (
            <button key={m} className={`chip ${m === mood ? "active" : ""}`} onClick={() => changeMood(m)}>{m}</button>
          ))}
        </div>
      )}

      {more.length > 0 && (
        <>
          <h3>More like this</h3>
          <ul className="song-list">
            {more.map((s) => (
              <li key={s.id}>
                <button className="song" onClick={() => play(s)}>
                  <img src={`https://i.ytimg.com/vi/${s.id}/mqdefault.jpg`} alt="" loading="lazy" />
                  <span>{s.title}<small>{s.channel}</small></span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
