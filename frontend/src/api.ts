export interface Plan {
  emotion: string;
  path: string[];
  target: string;
  affirmation: string | null;
}
export interface Song {
  id: string;
  title: string;
  channel: string;
}
export interface HistoryItem {
  id: number;
  session_id: string;
  emotion: string;
  confidence: number | null;
  detected_at: string;
}
export interface FaceResult {
  emotion: string;
  confidence: number;
  box: [number, number, number, number]; // x, y, w, h as 0-1 fractions of the frame
  scores: Record<string, number>;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  moods: () => request<{ moods: string[]; languages: string[] }>("/api/moods"),
  recordEmotion: (session_id: string, emotion: string, confidence: number | null) =>
    request<{ plan: Plan }>("/api/emotions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id, emotion, confidence }),
    }),
  plan: (emotion: string) => request<Plan>(`/api/mood/${encodeURIComponent(emotion)}`),
  songs: (mood: string, language: string, variant: number, limit = 8) =>
    request<{ songs: Song[] }>(
      `/api/music?mood=${encodeURIComponent(mood)}&language=${encodeURIComponent(language)}&variant=${variant}&limit=${limit}`,
    ),
  history: (sessionId?: string) =>
    request<{ items: HistoryItem[]; summary: Record<string, number> }>(
      `/api/history${sessionId ? `?session_id=${sessionId}` : ""}`,
    ),
  clearHistory: () => request<{ cleared: boolean }>("/api/history", { method: "DELETE" }),
};

export const MANUAL_EMOTIONS = ["Happy", "Sad", "Angry", "Fearful", "Neutral", "Surprised", "Disgusted"];
