import { NextResponse } from "next/server";

import { isAdminAuthenticated } from "@/lib/auth";
import llmConfig from "@/lib/mock/llm-config.json";

export async function GET() {
  if (!(await isAdminAuthenticated())) {
    return NextResponse.json(
      { ok: false, error: "未授权" },
      { status: 401 },
    );
  }
  return NextResponse.json({ ok: true, data: llmConfig, source: "mock" });
}

export async function PUT(request: Request) {
  if (!(await isAdminAuthenticated())) {
    return NextResponse.json(
      { ok: false, error: "未授权" },
      { status: 401 },
    );
  }

  const body = await request.json();

  // Mock: 返回更新后的配置
  const updated = {
    provider: body.provider ?? llmConfig.provider,
    apiKeyMasked: body.apiKey ? `****${body.apiKey.slice(-4)}` : llmConfig.apiKeyMasked,
    endpoint: body.endpoint ?? llmConfig.endpoint,
    modelName: body.modelName ?? llmConfig.modelName,
    isActive: true,
    updatedAt: new Date().toISOString(),
  };

  return NextResponse.json({ ok: true, data: updated, source: "mock" });
}
