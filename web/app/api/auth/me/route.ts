import { NextResponse } from "next/server";

import { getCurrentUser, isAdminAuthenticated } from "@/lib/auth";

export async function GET() {
  const user = await getCurrentUser();
  const admin = await isAdminAuthenticated();
  return NextResponse.json({
    ok: true,
    data: { user, admin },
    source: "mock",
  });
}
