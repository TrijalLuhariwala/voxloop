"use client";

import { useEffect, useRef, useState } from "react";
import {
  API_BASE_URL,
  openVoiceSocket,
  resetSession,
  type VoiceSocketMessage,
  type VoiceTurnResponse
} from "../lib/api";


function createNewSessionId(): string {
  return "session-" + Math.random().toString(36).substring(2, 10) + "-" + Date.now().toString(36);
}

export default function Home() {
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedTopic, setSelectedTopic] = useState("customer support");
  const [transcript, setTranscript] = useState("");
  const [result, setResult] = useState<VoiceTurnResponse | null>(null);
  const [chatHistory, setChatHistory] = useState<VoiceTurnResponse["memory"]>([]);
  const [isListening, setIsListening] = useState(false);
  const [status, setStatus] = useState("Ready for voice input");
  const [error, setError] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setSessionId(createNewSessionId());
  }, []);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatHistory, result]);

  async function startListening() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser does not support microphone audio capture.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;
      streamRef.current = stream;
      chunksRef.current = [];
      setError(null);
      setTranscript("");
      setStatus("Recording live voice input...");
      setIsListening(true);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsListening(false);
        setStatus("Sending audio stream over WebSocket...");
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        await sendAudioToBackend(blob);
      };

      recorder.start();
      window.setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
        }
      }, 5000);
    } catch {
      setIsListening(false);
      setError("Microphone access failed. Please check device permissions.");
    }
  }

  async function sendAudioToBackend(blob: Blob) {
    const audioBase64 = await blobToBase64(blob);
    const socket = openVoiceSocket();

    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          session_id: sessionId,
          selected_topic: selectedTopic,
          audio_base64: audioBase64,
          mime_type: blob.type || "audio/webm"
        })
      );
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as VoiceSocketMessage;
      if (message.type === "status") {
        setStatus(message.message);
        return;
      }
      if (message.type === "transcript") {
        setTranscript(message.transcript);
        setStatus("STT transcript generated. Running agent critique graph...");
        return;
      }
      if (message.type === "result") {
        setResult(message.payload);
        setChatHistory(message.payload.memory || []);
        setStatus("Turn completed.");
        setError(null);
        if (message.payload.tts_audio_url) {
          const rawUrl = message.payload.tts_audio_url;
          const fullAudioUrl = rawUrl.startsWith("http") ? rawUrl : `${API_BASE_URL}${rawUrl}`;
          if (audioRef.current) {
            audioRef.current.src = fullAudioUrl;
            void audioRef.current.play().catch(() => null);
          }
        }
        socket.close();
        return;
      }

      if (message.type === "error") {
        setError(message.message);
        setStatus("Workflow failed.");
        socket.close();
      }
    };

    socket.onerror = () => {
      setError("WebSocket connection error.");
      setStatus("Communication error.");
    };
  }

  async function handleResetSession() {
    if (!sessionId) return;
    try {
      setIsResetting(true);
      await resetSession(sessionId);
      const newId = createNewSessionId();
      setSessionId(newId);
      setChatHistory([]);
      setResult(null);
      setTranscript("");
      setError(null);
      setStatus("Session reset. Ready for new dialogue.");
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Failed to reset session.";
      setError(errMsg);
    } finally {
      setIsResetting(false);
    }
  }

  const scorecard = result?.critique.scorecard;

  return (
    <main className="shell">
      <div className="layout-grid">
        {/* Left Column: Main Controls & Active Turn Stage */}
        <div className="main-stage">
          {/* Header Panel */}
          <section className="panel header-panel">
            <div>
              <h1 className="brand-title">VoxLoop</h1>
              <p className="subtitle">
                A two-agent voice engine featuring continuous speech recognition, draft response generation, critic review scoring, and an improved synthesis pass.
              </p>
            </div>
            <div className="voice-status">
              <span className={`dot ${isListening ? "active" : ""}`} />
              <span>{status}</span>
            </div>
          </section>

          {/* Controls Bar */}
          <section className="panel">
            <div className="controls-bar">
              <label className="field">
                <span className="label">Agent Job / Persona Topic</span>
                <input
                  className="input"
                  value={selectedTopic}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                  placeholder="customer support, tech advisor, travel assistant..."
                />
              </label>
              <div className="button-group">
                <button
                  type="button"
                  className={`button button-speak ${isListening ? "recording" : ""}`}
                  onClick={startListening}
                  disabled={isListening || isResetting}
                >
                  {isListening ? (
                    <>
                      <span style={{ fontSize: "1.1rem" }}>🎙️</span> Listening...
                    </>
                  ) : (
                    <>
                      <span style={{ fontSize: "1.1rem" }}>🎙️</span> Speak
                    </>
                  )}
                </button>
                <button
                  type="button"
                  className="button button-reset"
                  onClick={handleResetSession}
                  disabled={isListening || isResetting}
                  title="Clear chat history and reset session memory"
                >
                  {isResetting ? "Resetting..." : "🔄 Reset Session"}
                </button>
              </div>
            </div>

            {transcript ? (
              <div className="card card-highlight" style={{ marginTop: 16 }}>
                <span className="label">Live Transcript</span>
                <div className="card-body">{transcript}</div>
              </div>
            ) : null}

            {error ? (
              <div className="error-banner" style={{ marginTop: 16 }}>
                ⚠️ {error}
              </div>
            ) : null}
            <audio ref={audioRef} hidden />
          </section>

          {/* Active Turn Results Stage */}
          {result ? (
            <>
              {/* Original vs Improved Response Grid */}
              <section className="panel">
                <span className="label" style={{ marginBottom: 12, display: "block" }}>
                  Agent Response Evaluation
                </span>
                <div className="response-grid">
                  <div className="card">
                    <div className="card-title-row">
                      <span className="label" style={{ color: "var(--muted)" }}>Original Response</span>
                      <span className="tag">Agent 1 Pass</span>
                    </div>
                    <div className="card-body">{result.original_response}</div>
                  </div>
                  <div className="card card-highlight">
                    <div className="card-title-row">
                      <span className="label" style={{ color: "var(--accent-cyan)" }}>Improved Response (Synthesized)</span>
                      <span className="tag" style={{ background: "rgba(0, 242, 254, 0.15)", color: "var(--accent-cyan)" }}>
                        Agent 2 Refined
                      </span>
                    </div>
                    <div className="card-body">{result.improved_response}</div>
                    {result.tts_audio_url ? (
                      <div style={{ marginTop: 12 }}>
                        <audio
                          controls
                          src={
                            result.tts_audio_url.startsWith("http")
                              ? result.tts_audio_url
                              : `${API_BASE_URL}${result.tts_audio_url}`
                          }
                          style={{ width: "100%", height: 36, borderRadius: 8 }}
                        />
                      </div>
                    ) : null}
                  </div>
                </div>
              </section>


              {/* Scorecard Progress Gauges */}
              <section className="panel">
                <span className="label" style={{ marginBottom: 14, display: "block" }}>
                  Critique Scorecard Matrix
                </span>
                <div className="scorecard-container">
                  <ScoreBar label="Accuracy" value={scorecard?.accuracy ?? 0} />
                  <ScoreBar label="Relevance" value={scorecard?.relevance ?? 0} />
                  <ScoreBar label="Empathy" value={scorecard?.empathy ?? 0} />
                  <ScoreBar label="Clarity" value={scorecard?.clarity ?? 0} />
                  <ScoreBar label="Policy" value={scorecard?.policy_compliance ?? 0} />
                  <ScoreBar label="Overall Score" value={scorecard?.overall ?? 0} />
                </div>
              </section>

              {/* Critique Insights & Suggestions */}
              <section className="panel">
                <div className="response-grid">
                  <div className="card">
                    <span className="label">Critique Reasoning</span>
                    <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: 6 }}>
                      Sentiment: <strong style={{ color: "var(--accent-teal)" }}>{result.critique.sentiment}</strong> | User State: <strong style={{ color: "var(--accent-cyan)" }}>{result.critique.user_state}</strong>
                    </div>
                    <div className="card-body">{result.critique.reasoning}</div>
                  </div>
                  <div className="card">
                    <span className="label">Actionable Suggestions</span>
                    <ul className="list-suggestions">
                      {result.critique.suggestions.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            </>
          ) : null}
        </div>

        {/* Right Column: Chat History Sidebar Panel */}
        <aside className="panel sidebar-panel">
          <div className="sidebar-header">
            <h2 className="sidebar-title">
              💬 Chat History
            </h2>
            <span className="badge">
              {chatHistory.length} {chatHistory.length === 1 ? "turn" : "turns"}
            </span>
          </div>

          <div className="chat-history-list" ref={chatScrollRef}>
            {chatHistory.length === 0 ? (
              <div className="empty-chat">
                <p style={{ margin: 0, fontSize: "1.5rem", marginBottom: 8 }}>🎤</p>
                <p style={{ margin: 0 }}>No dialogue turns recorded yet.</p>
                <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>
                  Click <strong>Speak</strong> to start a conversation.
                </p>
              </div>
            ) : (
              chatHistory.map((item, idx) => (
                <div key={idx} className="chat-turn">
                  {/* User Message Bubble */}
                  <div className="bubble bubble-user">
                    <div>{item.user_message}</div>
                    <div className="bubble-meta" style={{ justifyContent: "flex-end" }}>
                      <span>User</span> • <span>{formatTime(item.created_at)}</span>
                    </div>
                  </div>

                  {/* Agent Improved Response Bubble */}
                  <div className="bubble bubble-agent">
                    <div>{item.improved_response}</div>
                    <div className="bubble-meta">
                      <span style={{ color: "var(--accent-teal)", fontWeight: 600 }}>VoxLoop Agent</span>
                      <span className="tag">{item.sentiment}</span>
                      <span className="tag">{item.user_state}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const barClass = value >= 80 ? "high" : value >= 50 ? "mid" : "low";
  return (
    <div className="score-card">
      <div className="score-top">
        <span className="score-name">{label}</span>
        <span className="score-num">{value}</span>
      </div>
      <div className="progress-track">
        <div
          className={`progress-bar ${barClass}`}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Unable to read recorded audio blob."));
        return;
      }
      resolve(reader.result.split(",")[1] ?? "");
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

function formatTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}
