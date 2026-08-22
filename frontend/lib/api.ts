export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    if (window.location.port === "" || window.location.port === "80" || window.location.port === "443") {
      return `${protocol}//${window.location.host}`;
    }
    return `${protocol}//${hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

export function getWsBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_BASE_URL) {
    return process.env.NEXT_PUBLIC_WS_BASE_URL;
  }
  if (typeof window !== "undefined") {
    const isHttps = window.location.protocol === "https:";
    const wsProtocol = isHttps ? "wss:" : "ws:";
    const hostname = window.location.hostname;
    if (window.location.port === "" || window.location.port === "80" || window.location.port === "443") {
      return `${wsProtocol}//${window.location.host}`;
    }
    return `${wsProtocol}//${hostname}:8000`;
  }
  return "ws://127.0.0.1:8000";
}

export const API_BASE_URL = getApiBaseUrl();
export const WS_BASE_URL = getWsBaseUrl();



export type VoiceTurnResponse = {
  session_id: string;
  selected_topic: string;
  transcript: string;
  original_response: string;
  critique: {
    sentiment: string;
    user_state: string;
    scorecard: {
      accuracy: number;
      relevance: number;
      empathy: number;
      clarity: number;
      policy_compliance: number;
      overall: number;
    };
    suggestions: string[];
    reasoning: string;
  };
  improved_response: string;
  tts_audio_url: string;
  memory: Array<{
    user_message: string;
    original_response: string;
    improved_response: string;
    sentiment: string;
    user_state: string;
    created_at: string;
  }>;
};

export type VoiceSocketMessage =
  | { type: "status"; stage: string; message: string }
  | { type: "transcript"; transcript: string }
  | { type: "result"; payload: VoiceTurnResponse }
  | { type: "error"; message: string };

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function runVoiceTurn(input: {
  session_id: string;
  selected_topic: string;
  transcript: string;
}): Promise<VoiceTurnResponse> {
  return request<VoiceTurnResponse>("/api/voice-turn", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function resetSession(sessionId: string): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>("/api/reset-session", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId })
  });
}

export async function getSessionHistory(sessionId: string): Promise<{
  session_id: string;
  memory: VoiceTurnResponse["memory"];
}> {
  return request(`/api/session/${encodeURIComponent(sessionId)}/history`);
}

export function openVoiceSocket(): WebSocket {
  return new WebSocket(`${WS_BASE_URL}/ws/voice-turn`);
}

