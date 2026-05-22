import { NextResponse } from "next/server";

import { clearAdminSession, clearUserSession } from "@/lib/auth";

export async function POST() {
  await clearUserSession();
  await clearAdminSession();
  return NextResponse.json({ ok: true, source: "mock" });
}
