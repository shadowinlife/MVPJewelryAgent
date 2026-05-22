import { NextResponse } from "next/server";

import memberships from "@/lib/mock/memberships.json";

export async function GET() {
  return NextResponse.json({ ok: true, data: memberships, source: "mock" });
}
