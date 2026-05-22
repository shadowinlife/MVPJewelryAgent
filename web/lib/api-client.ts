import type { ApiResponse } from "@/lib/types/domain";

const isServer = typeof window === "undefined";

function resolveBase(): string {
  if (!isServer) return "";
  return process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:3000";
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResponse<T>> {
  const url = `${resolveBase()}${path}`;
  const res = await fetch(url, {
    cache: "no-store",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    return {
      ok: false,
      error:
        (body as { error?: string } | null)?.error ??
        `请求失败 (${res.status})`,
      source: "mock",
    };
  }

  return body as ApiResponse<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, payload?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: payload ? JSON.stringify(payload) : undefined,
    }),
  put: <T>(path: string, payload?: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: payload ? JSON.stringify(payload) : undefined,
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
