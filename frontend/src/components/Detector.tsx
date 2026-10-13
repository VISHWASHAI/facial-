import { useEffect, useRef, useState } from "react";
import { FaceResult, MANUAL_EMOTIONS } from "../api";

interface Props {
  busy: boolean;
  onResult: (emotion: string, confidence: number | null) => void;
}

const FRAME_WIDTH = 480;
const JPEG_QUALITY = 0.7;

export default function Detector({ busy, onResult }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const stopRef = useRef<(() => void) | null>(null);
  const [seconds, setSeconds] = useState(6);
  const [scanning, setScanning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [live, setLive] = useState<FaceResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // stop the camera if the component goes away mid-scan
  useEffect(() => () => stopRef.current?.(), []);

  function drawBox(face: FaceResult | null) {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!face) return;
    const [bx, by, bw, bh] = face.box;
    // the <video> is mirrored with CSS, so mirror the box x position to match
    const x = (1 - bx - bw) * canvas.width;
    const y = by * canvas.height;
    ctx.strokeStyle = "#22c55e";
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, bw * canvas.width, bh * canvas.height);
    ctx.fillStyle = "#22c55e";
    ctx.font = "bold 20px system-ui, sans-serif";
    ctx.fillText(`${face.emotion} ${face.confidence.toFixed(0)}%`, x, Math.max(y - 8, 20));
  }

  async function startScan() {
    setMessage(null);
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    } catch {
      setMessage("Could not open the webcam. Allow camera access and close other apps using it.");
      return;
    }
    const video = videoRef.current!;
    video.srcObject = stream;
    await video.play();

    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/analyze`);
    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = () => reject(new Error("ws"));
    }).catch(() => {
      stream.getTracks().forEach((t) => t.stop());
      setMessage("Could not reach the backend. Is the server running?");
    });
    if (ws.readyState !== WebSocket.OPEN) return;

    let running = true;
    const votes = new Map<string, number[]>();
    const capture = document.createElement("canvas");
    const cleanup = () => {
      running = false;
      ws.close();
      stream.getTracks().forEach((t) => t.stop());
      video.srcObject = null;
      drawBox(null);
      setScanning(false);
      setLive(null);
      stopRef.current = null;
    };
    stopRef.current = cleanup;
    setScanning(true);

    const startedAt = Date.now();
    const timer = setInterval(() => setTimeLeft(Math.max(0, seconds - Math.floor((Date.now() - startedAt) / 1000))), 250);

    // one frame in flight at a time: send, wait for the reply, send the next
    while (running && Date.now() - startedAt < seconds * 1000) {
      capture.width = FRAME_WIDTH;
      capture.height = Math.round((FRAME_WIDTH * video.videoHeight) / video.videoWidth);
      capture.getContext("2d")!.drawImage(video, 0, 0, capture.width, capture.height);
      const blob = await new Promise<Blob | null>((r) => capture.toBlob(r, "image/jpeg", JPEG_QUALITY));
      if (!blob || ws.readyState !== WebSocket.OPEN) break;
      const reply = await new Promise<{ face: FaceResult | null }>((resolve) => {
        ws.onmessage = (e) => resolve(JSON.parse(e.data));
        ws.onclose = () => resolve({ face: null });
        ws.send(blob);
      });
      drawBox(reply.face);
      setLive(reply.face);
      if (reply.face) {
        const list = votes.get(reply.face.emotion) ?? [];
        list.push(reply.face.confidence);
        votes.set(reply.face.emotion, list);
      }
    }
    clearInterval(timer);
    cleanup();

    if (votes.size === 0) {
      setMessage("No face detected. Face the camera, sit about an arm's length away, and use front lighting.");
      return;
    }
    // dominant emotion over the whole scan smooths out frame-to-frame noise
    const [emotion, confs] = [...votes.entries()].sort((a, b) => b[1].length - a[1].length)[0];
    onResult(emotion, Math.round((confs.reduce((s, c) => s + c, 0) / confs.length) * 10) / 10);
  }

  return (
    <section className="card">
      <h2>Detect your emotion</h2>
      <div className={`video-box ${scanning ? "on" : ""}`}>
        <video ref={videoRef} muted playsInline />
        <canvas ref={overlayRef} />
        {!scanning && <p className="muted">Camera preview appears here</p>}
      </div>
      {scanning && (
        <p className="status" aria-live="polite">
          Scanning… {timeLeft}s left {live ? `· seeing ${live.emotion}` : "· looking for a face"}
        </p>
      )}
      {message && <p className="error" role="alert">{message}</p>}
      <div className="row">
        <label>
          Scan length: {seconds}s
          <input type="range" min={3} max={15} value={seconds} disabled={scanning}
                 onChange={(e) => setSeconds(Number(e.target.value))} />
        </label>
        {scanning ? (
          <button className="secondary" onClick={() => stopRef.current?.()}>Stop</button>
        ) : (
          <button onClick={startScan} disabled={busy}>Start live detection</button>
        )}
      </div>
      <details>
        <summary>No camera? Pick how you feel</summary>
        <div className="chips">
          {MANUAL_EMOTIONS.map((e) => (
            <button key={e} className="chip" disabled={busy || scanning} onClick={() => onResult(e, null)}>{e}</button>
          ))}
        </div>
      </details>
    </section>
  );
}
