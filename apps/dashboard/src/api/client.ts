// Thin fetch wrapper shared by every service-specific api module. All
// requests go through the Vite dev-server proxy (see vite.config.ts) so
// the browser never needs CORS from the backend.

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function request<T>(
  base: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const body = await parseBody(res);
  if (!res.ok) {
    throw new ApiError(res.status, body);
  }
  return body as T;
}

export const AGENT_BASE = "/api/agent";
export const GATEWAY_BASE = "/api/gateway";
export const EXECUTOR_BASE = "/api/executor";
