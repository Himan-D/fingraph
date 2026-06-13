const API_URL = process.env.NEXT_PUBLIC_FINGRAPH_API_URL || "http://localhost:8000"

type ApiOptions = {
  token?: string
  signal?: AbortSignal
}

async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`
  }

  const res = await fetch(`${API_URL}${path}`, { headers, signal: options.signal })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || res.statusText)
  }

  return res.json() as Promise<T>
}

async function apiPost<T>(path: string, body: unknown, options: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal: options.signal,
  })

  if (!res.ok) {
    const resBody = await res.json().catch(() => ({}))
    throw new ApiError(res.status, resBody.detail || res.statusText)
  }

  return res.json() as Promise<T>
}

async function apiDelete<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: "DELETE",
    headers,
    signal: options.signal,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || res.statusText)
  }

  return res.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("fingraph_access_token")
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("fingraph_access_token", access)
  localStorage.setItem("fingraph_refresh_token", refresh)
}

export function clearTokens() {
  localStorage.removeItem("fingraph_access_token")
  localStorage.removeItem("fingraph_refresh_token")
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("fingraph_refresh_token")
}

export const api = {
  get: <T>(path: string, options?: ApiOptions) =>
    apiFetch<T>(path, { ...options, token: options?.token ?? getToken() ?? undefined }),

  post: <T>(path: string, body: unknown, options?: ApiOptions) =>
    apiPost<T>(path, body, { ...options, token: options?.token ?? getToken() ?? undefined }),

  delete: <T>(path: string, options?: ApiOptions) =>
    apiDelete<T>(path, { ...options, token: options?.token ?? getToken() ?? undefined }),
}

export type SSEEvent =
  | { type: "token"; content: string }
  | { type: "tool_start"; tool: string; args: Record<string, unknown> }
  | { type: "tool_end"; tool: string; result_preview: string }
  | { type: "done"; conversation_id: number; content: string }
  | { type: "error"; message: string }

export async function streamChat(
  message: string,
  conversationId?: number,
  symbol?: string,
): Promise<ReadableStream<Uint8Array>> {
  const token = getToken()
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}/api/v1/agent/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, conversation_id: conversationId, symbol }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || res.statusText)
  }

  if (!res.body) throw new Error("No response body")

  return res.body
}

export function parseSSELines(
  lines: string[],
): { events: SSEEvent[]; fullContent: string; finalContent?: string; conversationId?: number } {
  const events: SSEEvent[] = []
  let fullContent = ""
  let finalContent: string | undefined
  let conversationId: number | undefined

  for (const line of lines) {
    if (!line.startsWith("data: ")) continue
    try {
      const event = JSON.parse(line.slice(6)) as SSEEvent
      events.push(event)
      if (event.type === "token") fullContent += event.content
      if (event.type === "done") {
        finalContent = event.content
        conversationId = event.conversation_id
      }
    } catch {
      // skip unparseable lines
    }
  }

  return { events, fullContent, finalContent, conversationId }
}

export { API_URL }
