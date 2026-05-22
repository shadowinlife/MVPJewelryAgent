import { NextResponse } from "next/server";

import { setAdminSession, verifyAdmin } from "@/lib/auth";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as
    | { username?: string; password?: string }
    | null;

  if (!body?.username || !body?.password) {
    return NextResponse.json(
      { ok: false, error: "请输入账号和密码", source: "mock" },
      { status: 400 },
    );
  }

  if (!verifyAdmin(body.username, body.password)) {
    return NextResponse.json(
      { ok: false, error: "账号或密码错误", source: "mock" },
      { status: 401 },
    );
  }

  await setAdminSession();
  return NextResponse.json({
    ok: true,
    data: { username: body.username },
    source: "mock",
  });
}
