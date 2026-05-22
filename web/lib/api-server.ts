import "server-only";
import { cookies } from "next/headers";

import type { ApiResponse } from "@/lib/types/domain";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:3000";

async function cookieHeader(): Promise<string | null> {
  // Server components / route handlers calling our own routes 时,浏览器 Cookie
  // 不会自动转发。这里把当前请求的 Cookie 头打包后塞回去,保住会话。
  try {
    const jar = await cookies();
    const pairs = jar
      .getAll()
      .map((c) => `${c.name}=${encodeURIComponent(c.value)}`);
    return pairs.length ? pairs.join("; ") : null;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResponse<T>> {
  const url = `${BASE}${path}`;
  const ck = await cookieHeader();
  const res = await fetch(url, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(ck ? { cookie: ck } : {}),
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

export const serverApi = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, payload?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: payload ? JSON.stringify(payload) : undefined,
    }),
};
