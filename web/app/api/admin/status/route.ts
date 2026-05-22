import { NextResponse } from "next/server";

import adminStatus from "@/lib/mock/admin-status.json";

export async function GET() {
  return NextResponse.json({ ok: true, data: adminStatus, source: "mock" });
}
