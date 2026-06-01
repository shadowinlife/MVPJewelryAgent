import { LLMConfigForm } from "@/components/admin/llm-config-form";

export default function LLMConfigPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">LLM 服务商配置</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          配置 AI 模型调用通道 — 切换 Provider 无需重新部署
        </p>
      </div>
      <LLMConfigForm />
    </div>
  );
}
