"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { MessageCircle, ShieldCheck, Smartphone } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MockBadge } from "@/components/yaoqi";
import { apiClient } from "@/lib/api-client";

export function LoginForm() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [otpSent, setOtpSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [pending, startTransition] = useTransition();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const phoneValid = /^1[3-9]\d{9}$/.test(phone);
  const otpValid = /^\d{6}$/.test(otp);

  function handleSendOtp() {
    if (!phoneValid) {
      setError("请输入正确的 11 位手机号(1 开头)");
      return;
    }
    setError(null);
    setOtpSent(true);
    setCountdown(60);
    // Mock:任意 6 位数字都能登录,不真实发送
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!agreed) {
      setError("请先勾选同意服务条款与隐私政策");
      return;
    }
    if (!phoneValid) {
      setError("请输入正确的手机号");
      return;
    }
    if (!otpValid) {
      setError("请输入 6 位数字验证码");
      return;
    }
    setError(null);
    setSubmitting(true);
    const res = await apiClient.post<{ user: { id: string } }>(
      "/api/auth/login",
      { phone, otp },
    );
    setSubmitting(false);
    if (!res.ok) {
      setError(res.error ?? "登录失败,请稍后再试");
      return;
    }
    startTransition(() => {
      router.replace("/dashboard");
      router.refresh();
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div className="space-y-1.5">
        <Label htmlFor="phone" className="text-sm">
          手机号
        </Label>
        <div className="relative">
          <Smartphone
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            id="phone"
            inputMode="numeric"
            autoComplete="tel"
            maxLength={11}
            placeholder="11 位手机号 (13 开头任意手机号即可)"
            value={phone}
            onChange={(e) => setPhone(e.target.value.replace(/[^\d]/g, ""))}
            className="pl-9"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="otp" className="text-sm">
          验证码
        </Label>
        <div className="flex gap-2">
          <Input
            id="otp"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            placeholder="6 位数字"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/[^\d]/g, ""))}
          />
          <Button
            type="button"
            variant="outline"
            disabled={!phoneValid || countdown > 0}
            onClick={handleSendOtp}
            className="cursor-pointer whitespace-nowrap"
          >
            {countdown > 0
              ? `${countdown}s 后重发`
              : otpSent
                ? "重新获取"
                : "获取验证码"}
          </Button>
        </div>
        {otpSent ? (
          <p className="text-[11px] text-muted-foreground">
            Mock 模式 · 任意 6 位数字均可登录,演示用户为{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-[10px]">
              {phone || "1380000000x"}
            </code>
          </p>
        ) : null}
      </div>

      <div className="flex items-start gap-2 pt-1">
        <Checkbox
          id="agree"
          checked={agreed}
          onCheckedChange={(v) => setAgreed(v === true)}
          className="mt-0.5 cursor-pointer"
        />
        <Label
          htmlFor="agree"
          className="text-xs leading-relaxed text-muted-foreground"
        >
          我已阅读并同意《服务条款》《隐私政策》《AI 辅助判断免责声明》
        </Label>
      </div>

      {error ? (
        <p
          role="alert"
          className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive"
        >
          {error}
        </p>
      ) : null}

      <Button
        type="submit"
        className="w-full cursor-pointer"
        disabled={submitting || pending}
      >
        {submitting || pending ? "登录中…" : "登录 / 注册"}
      </Button>

      <div className="flex items-center justify-between gap-3 pt-1">
        <Button
          type="button"
          variant="ghost"
          className="cursor-not-allowed text-xs text-muted-foreground"
          disabled
        >
          <MessageCircle className="mr-1.5 h-4 w-4" aria-hidden />
          微信登录
        </Button>
        <MockBadge status="later" label="微信待接入" />
      </div>

      <p className="flex items-center gap-1.5 pt-2 text-[11px] text-muted-foreground">
        <ShieldCheck className="h-3 w-3" aria-hidden />
        Mock 凭证仅本地使用,任何真实接入需配置 OTP 服务商
      </p>
    </form>
  );
}
