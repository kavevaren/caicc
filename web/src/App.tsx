import { useCallback, useEffect, useRef, useState } from "react";
import { AtomLoader } from "./components/atom/AtomLoader";

type Health = {
  server: string;
  modelscope: string;
  modelscope_latency_ms: number;
  whisper: string;
  version: string;
};

type SseEvent = { n: number; at: number };

type SseState = {
  running: boolean;
  events: SseEvent[];
  detail: string;
  verdict: "" | "ok" | "bad";
};

type UploadSize = 10 | 50 | 100 | 200;
type UploadResult = { ok: boolean; detail: string };
type UploadState = { running: boolean; results: Partial<Record<UploadSize, UploadResult>> };

type Probe = { ok: boolean; detail: string };

const UPLOAD_SIZES: UploadSize[] = [10, 50, 100, 200];

function statusLabel(v: string) {
  const ok = ["ok", "ready"];
  const bad = ["down", "invalid_token", "unreachable", "error"];
  const cls = ok.includes(v) ? "ok" : bad.includes(v) ? "bad" : "pending";
  return <span className={cls}>{v}</span>;
}

/** One 1 MiB random block, repeated — a 200 MB Blob without 200 MB of randomness. */
function makeBlob(mb: number): Blob {
  const block = new Uint8Array(1024 * 1024);
  crypto.getRandomValues(block.subarray(0, 32768));
  for (let i = 32768; i < block.length; i += 32768) {
    block.set(block.subarray(0, 32768), i);
  }
  const parts: BlobPart[] = [];
  for (let i = 0; i < mb; i += 25) {
    const take = Math.min(25, mb - i);
    const slice = new Uint8Array(take * 1024 * 1024);
    for (let b = 0; b < take; b++) slice.set(block, b * 1024 * 1024);
    parts.push(slice);
  }
  return new Blob(parts);
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState("");
  const [sse, setSse] = useState<SseState>({ running: false, events: [], detail: "", verdict: "" });
  const [upload, setUpload] = useState<UploadState>({ running: false, results: {} });
  const [mic, setMic] = useState<Probe & { level: number }>({ ok: false, level: 0, detail: "Belum diuji" });
  const [storage, setStorage] = useState<Probe>({ ok: false, detail: "Belum diuji" });
  const [publicUrl, setPublicUrl] = useState("");
  const micRef = useRef<{ ctx: AudioContext; stream: MediaStream } | null>(null);

  // Theme follows system preference; the choice is stored in localStorage.
  useEffect(() => {
    const saved = localStorage.getItem("orvina-theme") as "light" | "dark" | null;
    const t = saved ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.dataset.theme = t;
  }, []);

  const toggleTheme = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("orvina-theme", next);
  };

  // --- health (server caches the ModelScope probe for 5 min) -----------------
  const loadHealth = useCallback(async () => {
    try {
      const r = await fetch("/api/health", { cache: "no-store" });
      setHealth((await r.json()) as Health);
      setHealthError("");
    } catch (e) {
      setHealthError(String(e));
    }
  }, []);

  useEffect(() => {
    loadHealth();
    const t = setInterval(loadHealth, 5000);
    return () => clearInterval(t);
  }, [loadHealth]);

  // --- localStorage probe -----------------------------------------------------
  useEffect(() => {
    try {
      localStorage.setItem("__orvina_probe__", "ok");
      const v = localStorage.getItem("__orvina_probe__");
      localStorage.removeItem("__orvina_probe__");
      setStorage(v === "ok" ? { ok: true, detail: "tulis dan baca berhasil" } : { ok: false, detail: "nilai yang dibacakan tidak cocok" });
    } catch (e) {
      setStorage({ ok: false, detail: String(e) });
    }
  }, []);

  // --- PUBLIC_APP_URL for "Buka di tab baru" (P0-only config endpoint) --------
  useEffect(() => {
    fetch("/api/probe/config")
      .then((r) => r.json())
      .then((j: { public_app_url: string }) => setPublicUrl(j.public_app_url ?? ""))
      .catch(() => setPublicUrl(""));
  }, []);

  const openUrl = publicUrl || window.location.origin;

  // --- SSE probe: one tick per second for 20 s --------------------------------
  const runSse = async () => {
    if (sse.running) return;
    setSse({ running: true, events: [], detail: "", verdict: "" });
    const t0 = performance.now();
    const ctrl = new AbortController();
    const timeout = setTimeout(() => ctrl.abort(), 30000);
    try {
      const r = await fetch("/api/probe/sse", { cache: "no-store", signal: ctrl.signal });
      if (!r.ok || !r.body) throw new Error(`status ${r.status}`);
      const reader = r.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      const events: SseEvent[] = [];
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let idx: number;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          const frame = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          let ev = "message";
          let data = "";
          for (const line of frame.split("\n")) {
            if (line.startsWith("event:")) ev = line.slice(6).trim();
            else if (line.startsWith("data:")) data = line.slice(5).trim();
          }
          if (ev === "tick" && data) {
            const j = JSON.parse(data) as { n: number };
            events.push({ n: j.n, at: Math.round(performance.now() - t0) });
            setSse((s) => ({ ...s, events: [...events] }));
          }
        }
      }
      const gaps = events.slice(1).map((e, i) => e.at - events[i].at);
      const median = gaps.length ? [...gaps].sort((a, b) => a - b)[Math.floor(gaps.length / 2)] : 0;
      const verdict: SseState["verdict"] = events.length === 20 && median >= 400 ? "ok" : "bad";
      const detail =
        events.length === 20
          ? `20 event diterima; median selang antar-event ${median} ms → ${
              median >= 400 ? "teririm 1 per detik (proxy tidak membuffer)" : "datang bergerombol (proxy membuffer)"
            }`
          : `hanya ${events.length} dari 20 event yang sampai`;
      setSse({ running: false, events, detail, verdict });
    } catch (e) {
      setSse((s) => ({ ...s, running: false, detail: `gagal: ${String(e)}`, verdict: "bad" }));
    } finally {
      clearTimeout(timeout);
    }
  };

  // --- upload probe ------------------------------------------------------------
  const runUpload = async (size: UploadSize) => {
    if (upload.running) return;
    setUpload((u) => ({ ...u, running: true, results: { ...u.results, [size]: { ok: false, detail: "Mengirim…" } } }));
    const t0 = performance.now();
    try {
      const blob = makeBlob(size);
      const r = await fetch("/api/probe/upload", { method: "POST", body: blob });
      const j = (await r.json()) as { received_bytes?: number; error?: { code: string } };
      const secs = ((performance.now() - t0) / 1000).toFixed(1);
      const want = size * 1024 * 1024;
      if (r.ok && j.received_bytes === want) {
        setUpload((u) => ({ ...u, running: false, results: { ...u.results, [size]: { ok: true, detail: `${j.received_bytes} byte utuh dalam ${secs} d` } } }));
      } else {
        setUpload((u) => ({ ...u, running: false, results: { ...u.results, [size]: { ok: false, detail: `status ${r.status} setelah ${secs} d — ${JSON.stringify(j)}` } } }));
      }
    } catch (e) {
      setUpload((u) => ({ ...u, running: false, results: { ...u.results, [size]: { ok: false, detail: `gagal setelah ${((performance.now() - t0) / 1000).toFixed(1)} d — ${String(e)}` } } }));
    }
  };

  // --- mic level meter -----------------------------------------------------------
  const testMic = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext({ sampleRate: 16000 });
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      src.connect(analyser);
      micRef.current = { ctx, stream };
      const buf = new Uint8Array(analyser.fftSize);
      let stopped = false;
      const tick = () => {
        if (stopped) return;
        analyser.getByteTimeDomainData(buf);
        let sum = 0;
        for (let i = 0; i < buf.length; i++) {
          const v = (buf[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / buf.length);
        setMic({ ok: true, level: Math.min(1, rms * 4), detail: `sample rate ${ctx.sampleRate}` });
        setTimeout(tick, 100);
      };
      tick();
      setMic((m) => ({ ...m, ok: true, detail: `sample rate ${ctx.sampleRate}` }));
    } catch (e) {
      setMic({ ok: false, level: 0, detail: String(e) });
    }
  };

  const stopMic = () => {
    micRef.current?.stream.getTracks().forEach((t) => t.stop());
    void micRef.current?.ctx.close();
    micRef.current = null;
    setMic((m) => ({ ok: m.ok, level: 0, detail: `${m.detail} (dihentikan)` }));
  };

  useEffect(() => () => stopMic(), []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="page">
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
        <h1 style={{ margin: 0 }}>P0 Platform Probe · Orvina</h1>
        <button onClick={toggleTheme}>{document.documentElement.dataset.theme === "dark" ? "Tema terang" : "Tema gelap"}</button>
      </div>
      <p className="meta">Satu image Docker (Python FastAPI + React) di Studio CPU gratis. Uji SSE, unggahan, mikrofon, dan penyimpanan.</p>

      <div className="card">
        <div className="atom-row">
          <AtomLoader size={56} />
          <div>
            <h2 style={{ margin: 0 }}>Health</h2>
            {health ? (
              <p style={{ margin: 4 }}>
                server {statusLabel(health.server)} · modelscope {statusLabel(health.modelscope)} ({health.modelscope_latency_ms} ms) · whisper{" "}
                {statusLabel(health.whisper)}
              </p>
            ) : (
              <p className="pending" style={{ margin: 4 }}>{healthError || "Memuat…"}</p>
            )}
            {health && <pre>{JSON.stringify(health, null, 2)}</pre>}
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Uji SSE (20 event, 1 per detik)</h2>
        <button className="primary" onClick={runSse} disabled={sse.running}>
          {sse.running ? "Berjalan…" : "Uji SSE"}
        </button>
        {sse.events.length > 0 && (
          <table className="results" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Event</th>
                <th>Tiba (ms)</th>
                <th>Selang (ms)</th>
              </tr>
            </thead>
            <tbody>
              {sse.events.map((e, i) => (
                <tr key={e.n}>
                  <td>{e.n}/20</td>
                  <td>{e.at}</td>
                  <td>{i === 0 ? "—" : e.at - sse.events[i - 1].at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {sse.detail && <p style={{ marginTop: 8 }} className={sse.verdict === "ok" ? "ok" : sse.verdict === "bad" ? "bad" : "pending"}>{sse.detail}</p>}
      </div>

      <div className="card">
        <h2>Uji unggahan (blob acak)</h2>
        <div className="row">
          {UPLOAD_SIZES.map((s) => (
            <button key={s} onClick={() => runUpload(s)} disabled={upload.running}>
              {upload.results[s] ? `${s} MB: ${upload.results[s]!.detail}` : `${s} MB`}
            </button>
          ))}
        </div>
        <p className="meta" style={{ marginTop: 8 }}>Server tidak menyimpan apa pun; hanya menghitung byte. Hasil menentukan MAX_UPLOAD_MB di P1.</p>
      </div>

      <div className="card">
        <h2>Mikrofon (level suara)</h2>
        <div className="row">
          {mic.ok ? (
            <button onClick={stopMic}>Hentikan mikrofon</button>
          ) : (
            <button className="primary" onClick={testMic}>Uji mikrofon</button>
          )}
          <span className="meta">{mic.detail}</span>
        </div>
        {mic.ok && (
          <div className="meter" aria-label="Level suara" style={{ marginTop: 12 }}>
            <div style={{ width: `${Math.round(mic.level * 100)}%` }} />
          </div>
        )}
      </div>

      <div className="card">
        <h2>localStorage</h2>
        <p style={{ margin: 0 }}>
          {storage.ok ? <span className="ok">OK</span> : <span className="bad">Gagal</span>} <span className="meta">{storage.detail}</span>
        </p>
      </div>

      <div className="card">
        <h2>Buka di tab baru</h2>
        <p style={{ margin: 0 }}>
          <a href={openUrl} target="_blank" rel="noreferrer">
            {openUrl}
          </a>
          {!publicUrl && <span className="meta"> — PUBLIC_APP_URL belum diset; memakai origin saat ini.</span>}
        </p>
      </div>
    </div>
  );
}
