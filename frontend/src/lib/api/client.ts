/**
 * REST client for ScholarAI/GrantPath backend.
 * - Bearer token injection
 * - Silent refresh 60s before access-token expiry
 * - Single 401 retry after refresh
 * - Typed errors with `.code` for UI branching
 * - Thin: no global state beyond token store; AuthProvider owns lifecycle
 */

const STORAGE_ACCESS = "grantpath.access_token";
const STORAGE_REFRESH = "grantpath.refresh_token";
const STORAGE_EXPIRES = "grantpath.access_expires_at";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
  "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Tokens = {
  access: string;
  refresh: string;
  expiresAt: number;
};

let memoryTokens: Tokens | null = null;
let inflightRefresh: Promise<Tokens | null> | null = null;
const listeners = new Set<(t: Tokens | null) => void>();

function readStored(): Tokens | null {
  if (typeof window === "undefined") return null;
  const access = localStorage.getItem(STORAGE_ACCESS);
  const refresh = localStorage.getItem(STORAGE_REFRESH);
  const expires = Number(localStorage.getItem(STORAGE_EXPIRES) || 0);
  if (!access || !refresh) return null;
  return { access, refresh, expiresAt: expires };
}

export function getTokens(): Tokens | null {
  if (memoryTokens) return memoryTokens;
  memoryTokens = readStored();
  return memoryTokens;
}

export function setTokens(t: Tokens | null) {
  memoryTokens = t;
  if (typeof window === "undefined") return;
  if (t) {
    localStorage.setItem(STORAGE_ACCESS, t.access);
    localStorage.setItem(STORAGE_REFRESH, t.refresh);
    localStorage.setItem(STORAGE_EXPIRES, String(t.expiresAt));
  } else {
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_EXPIRES);
  }
  listeners.forEach((fn) => fn(t));
}

export function subscribeTokens(fn: (t: Tokens | null) => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

async function refreshTokens(): Promise<Tokens | null> {
  if (inflightRefresh) return inflightRefresh;
  const current = getTokens();
  if (!current?.refresh) return null;

  inflightRefresh = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: current.refresh }),
      });
      if (!res.ok) {
        setTokens(null);
        return null;
      }
      const data = (await res.json()) as {
        access_token: string;
        refresh_token?: string;
        expires_in?: number;
      };
      const next: Tokens = {
        access: data.access_token,
        refresh: data.refresh_token ?? current.refresh,
        expiresAt: Date.now() + (data.expires_in ?? 3600) * 1000,
      };
      setTokens(next);
      return next;
    } catch {
      return null;
    } finally {
      inflightRefresh = null;
    }
  })();
  return inflightRefresh;
}

function shouldPreemptivelyRefresh(t: Tokens | null): boolean {
  if (!t) return false;
  return t.expiresAt - Date.now() < 60_000;
}

export type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  formData?: FormData;
  signal?: AbortSignal;
  auth?: boolean;
};

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(path.startsWith("http") ? path : `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

export async function apiRequest<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, formData, signal, auth = true } = opts;

  let tokens = getTokens();
  if (auth && shouldPreemptivelyRefresh(tokens)) {
    tokens = (await refreshTokens()) ?? tokens;
  }

  const headers: Record<string, string> = {};
  if (!formData) headers["Content-Type"] = "application/json";
  if (auth && tokens?.access) headers["Authorization"] = `Bearer ${tokens.access}`;

  const init: RequestInit = {
    method,
    headers,
    signal,
    cache: "no-store",
    body: formData ? formData : body !== undefined ? JSON.stringify(body) : undefined,
  };

  let res = await fetch(buildUrl(path, query), init);

  if (res.status === 401 && auth && getTokens()?.refresh) {
    const refreshed = await refreshTokens();
    if (refreshed?.access) {
      headers["Authorization"] = `Bearer ${refreshed.access}`;
      res = await fetch(buildUrl(path, query), { ...init, headers });
    }
  }

  if (res.status === 204) return undefined as T;

  let payload: unknown = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    payload = await res.json().catch(() => null);
  } else {
    payload = await res.text().catch(() => null);
  }

  if (!res.ok) {
    const detail = (payload as { detail?: unknown })?.detail ?? payload;
    const message =
      typeof detail === "string"
        ? detail
        : (payload as { message?: string })?.message || res.statusText || "Request failed";
    const code = (payload as { code?: string })?.code || `http_${res.status}`;
    throw new ApiError(res.status, code, message, detail);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, opts?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...opts, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...opts, method: "PATCH", body }),
  put: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...opts, method: "PUT", body }),
  delete: <T>(path: string, opts?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...opts, method: "DELETE" }),
  upload: <T>(path: string, formData: FormData, opts?: Omit<RequestOptions, "method" | "body" | "formData">) =>
    apiRequest<T>(path, { ...opts, method: "POST", formData }),
};
