"use client";

import { useEffect, useState } from "react";
import { Bot, CheckCircle, XCircle, Loader2 } from "lucide-react";

import { apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

type Provider = "dashscope" | "azure_openai";

interface LLMConfig {
  provider: Provider;
  apiKeyMasked: string;
  endpoint: string;
  modelName: string;
  isActive: boolean;
  updatedAt: string | null;
}

const PROVIDER_DEFAULTS: Record<
  Provider,
  { endpoint: string; modelPlaceholder: string }
> = {
  dashscope: {
    endpoint: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    modelPlaceholder: "qwen3.7-max / qwen-max / qwen-plus",
  },
  azure_openai: {
    endpoint: "https://your-resource.openai.azure.com/",
    modelPlaceholder: "gpt-4o-mini / gpt-4o",
  },
};

export function LLMConfigForm() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const [provider, setProvider] = useState<Provider>("dashscope");
  const [apiKey, setApiKey] = useState("");
  const [endpoint, setEndpoint] = useState(PROVIDER_DEFAULTS.dashscope.endpoint);
  const [modelName, setModelName] = useState("");
  const [currentMaskedKey, setCurrentMaskedKey] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    setLoading(true);
    const res = await apiClient.get<LLMConfig>("/api/admin/llm-config");
    if (res.ok && res.data) {
      setProvider(res.data.provider);
      setEndpoint(res.data.endpoint);
      setModelName(res.data.modelName);
      setCurrentMaskedKey(res.data.apiKeyMasked);
      setUpdatedAt(res.data.updatedAt);
    }
    setLoading(false);
  }

  function handleProviderChange(value: string | null) {
    if (!value) return;
    const p = value as Provider;
    setProvider(p);
    setEndpoint(PROVIDER_DEFAULTS[p].endpoint);
    setTestResult(null);
    setSaveMessage(null);
  }

  async function handleSave() {
    setSaving(true);
    setSaveMessage(null);
    setTestResult(null);

    const payload: Record<string, unknown> = {
      provider,
      endpoint,
      modelName,
    };
    if (apiKey) {
      payload.apiKey = apiKey;
    }

    const res = await apiClient.put<LLMConfig>("/api/admin/llm-config", payload);
    if (res.ok && res.data) {
      setCurrentMaskedKey(res.data.apiKeyMasked);
      setUpdatedAt(res.data.updatedAt);
      setApiKey("");
      setSaveMessage("配置已保存");
    } else {
      setSaveMessage(res.error ?? "保存失败");
    }
    setSaving(false);
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);

    const res = await apiClient.post<{
      success: boolean;
      latencyMs: number | null;
      modelResponse: string | null;
      error: string | null;
    }>("/api/admin/llm-config/test");

    if (res.ok && res.data) {
      setTestResult({
        success: res.data.success,
        message: res.data.success
          ? `连接成功 (${res.data.latencyMs}ms) — "${res.data.modelResponse}"`
          : `连接失败: ${res.data.error}`,
      });
    } else {
      setTestResult({ success: false, message: res.error ?? "测试请求失败" });
    }
    setTesting(false);
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <Bot className="h-5 w-5 text-primary" />
          <div>
            <CardTitle>Provider 配置</CardTitle>
            <CardDescription>
              当前使用:{" "}
              <Badge variant="secondary">
                {provider === "dashscope" ? "DashScope 通义千问" : "Azure OpenAI"}
              </Badge>
              {currentMaskedKey && (
                <span className="ml-2 text-xs text-muted-foreground">
                  Key: {currentMaskedKey}
                </span>
              )}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          {/* Provider */}
          <div className="space-y-1.5">
            <Label htmlFor="provider">Provider</Label>
            <Select value={provider} onValueChange={handleProviderChange}>
              <SelectTrigger id="provider">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dashscope">
                  DashScope (通义千问)
                </SelectItem>
                <SelectItem value="azure_openai">Azure OpenAI</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model Name */}
          <div className="space-y-1.5">
            <Label htmlFor="model-name">模型名称</Label>
            <Input
              id="model-name"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder={PROVIDER_DEFAULTS[provider].modelPlaceholder}
            />
          </div>

          {/* API Key */}
          <div className="space-y-1.5">
            <Label htmlFor="api-key">
              API Key{" "}
              {currentMaskedKey && (
                <span className="text-xs text-muted-foreground">
                  (留空保留现有: {currentMaskedKey})
                </span>
              )}
            </Label>
            <Input
              id="api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="输入新 Key 或留空保留原值"
            />
          </div>

          {/* Endpoint */}
          <div className="space-y-1.5">
            <Label htmlFor="endpoint">Endpoint</Label>
            <Input
              id="endpoint"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder={PROVIDER_DEFAULTS[provider].endpoint}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} disabled={saving || !modelName || !endpoint}>
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            保存配置
          </Button>
          <Button variant="outline" onClick={handleTest} disabled={testing}>
            {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            测试连通性
          </Button>
          {updatedAt && (
            <span className="text-xs text-muted-foreground">
              最后更新: {new Date(updatedAt).toLocaleString("zh-CN")}
            </span>
          )}
        </div>

        {/* Feedback */}
        {saveMessage && (
          <p className="text-sm text-green-600">{saveMessage}</p>
        )}
        {testResult && (
          <div
            className={`flex items-center gap-2 rounded-md p-3 text-sm ${
              testResult.success
                ? "bg-green-50 text-green-700"
                : "bg-red-50 text-red-700"
            }`}
          >
            {testResult.success ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            {testResult.message}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
