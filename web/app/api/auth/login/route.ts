import { NextResponse } from "next/server";

import {
  findUserByPhone,
  setUserSession,
  validateOtp,
  validatePhone,
} from "@/lib/auth";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as
    | { phone?: string; otp?: string }
    | null;

  if (!body?.phone || !body?.otp) {
    return NextResponse.json(
      { ok: false, error: "缺少手机号或验证码", source: "mock" },
      { status: 400 },
    );
  }

  if (!validatePhone(body.phone)) {
    return NextResponse.json(
      { ok: false, error: "手机号格式不正确", source: "mock" },
      { status: 400 },
    );
  }

  if (!validateOtp(body.otp)) {
    return NextResponse.json(
      { ok: false, error: "验证码需为 6 位数字", source: "mock" },
      { status: 400 },
    );
  }

  const user = findUserByPhone(body.phone);
  await setUserSession(user.id);

  return NextResponse.json({ ok: true, data: user, source: "mock" });
}
