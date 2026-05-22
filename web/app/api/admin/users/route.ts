import { NextResponse } from "next/server";

import usersData from "@/lib/mock/users.json";
import { isAdminAuthenticated } from "@/lib/auth";

export async function GET() {
  if (!(await isAdminAuthenticated())) {
    return NextResponse.json(
      { ok: false, error: "需要管理员登录", source: "mock" },
      { status: 401 },
    );
  }
  return NextResponse.json({
    ok: true,
    data: usersData.users,
    source: "mock",
  });
}
