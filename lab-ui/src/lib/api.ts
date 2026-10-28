import { useCallback, useEffect, useState } from "react";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function describe(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const d = data as { detail?: unknown; errors?: unknown[] };
    if (typeof d.detail === "string") return d.detail;
    if (Array.isArray(d.detail))
      return d.detail
        .map((e: { loc?: unknown[]; msg?: string }) =>
          [e.loc?.filter((p) => p !== "body").join("."), e.msg?.replace(/^Value error, /, "")]
            .filter(Boolean)
            .join(" : "),
        )
        .join(" · ");
    if (Array.isArray(d.errors)) return `${d.errors.length} ligne(s) invalide(s) : rien n'a été importé`;
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const isJson = init.body !== undefined && !(init.body instanceof FormData);
  const res = await fetch(path, {
    ...init,
    headers: isJson ? { "Content-Type": "application/json", ...init.headers } : init.headers,
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new ApiError(res.status, describe(data, `${res.status} ${res.statusText}`), data);
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
    }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: (path: string) => request<void>(path, { method: "DELETE" }),
};

export function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params))
    if (value !== null && value !== undefined && value !== "") search.set(key, String(value));
  const s = search.toString();
  return s ? `?${s}` : "";
}

/** Charge une ressource GET ; `reload` permet de la rafraîchir après une action. */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setLoading(true);
    api
      .get<T>(path)
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [path, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload, setData };
}
