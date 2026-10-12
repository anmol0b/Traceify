import type { ChatMessage, ProfileResponse } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    if (typeof body?.message === "string") return new ApiError(res.status, body.code ?? "error", body.message);
    if (Array.isArray(body?.detail)) return new ApiError(res.status, "invalid_request", "That request wasn't valid.");
  } catch {
    // fall through
  }
  return new ApiError(res.status, "error", `Request failed (HTTP ${res.status}).`);
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "network", "Can't reach the Traceify API. Is the backend running?");
  }
  if (!res.ok) throw await toApiError(res);
  return res;
}

export async function getProfile(handle: string, signal?: AbortSignal): Promise<ProfileResponse> {
  return (await request(`/api/profiles/${encodeURIComponent(handle)}`, { signal })).json();
}

export async function refreshProfile(handle: string): Promise<ProfileResponse> {
  return (await request(`/api/profiles/${encodeURIComponent(handle)}/refresh`, { method: "POST" })).json();
}

/** POST a question and stream the plain-text answer chunk by chunk. */
export async function streamChat(
  handle: string,
  question: string,
  history: ChatMessage[],
  onChunk: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await request("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle, question, history }),
    signal,
  });
  if (!res.body) {
    onChunk(await res.text());
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
  const tail = decoder.decode();
  if (tail) onChunk(tail);
}

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en", { notation: value >= 10_000 ? "compact" : "standard" }).format(value);
}
