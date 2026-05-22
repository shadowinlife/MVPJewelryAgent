import type { Metadata } from "next";
import Link from "next/link";

import { BrandLogo, DisclaimerNote, MockBadge } from "@/components/yaoqi";

import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "登录 · 曜齐 YAOQI",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-8 px-5 py-12 md:max-w-lg md:px-8">
        <header className="flex flex-col items-center gap-3 text-center">
          <BrandLogo size="lg" withTagline />
          <p className="text-sm text-muted-foreground">
            AI 珠宝鉴定估价辅助工具 · 玉石 / 珠宝品类
          </p>
        </header>

        <section className="rounded-2xl border border-border bg-card/80 p-6 shadow-sm md:p-8">
          <div className="mb-5 flex items-center justify-between">
            <h1 className="font-serif text-xl">登录 / 注册</h1>
            <MockBadge status="mock" label="Mock 登录" />
          </div>
          <LoginForm />
        </section>

        <footer className="space-y-3">
          <DisclaimerNote variant="block" />
          <p className="text-center text-[11px] text-muted-foreground">
            登录即表示同意{" "}
            <Link className="underline underline-offset-2" href="#">
              服务条款
            </Link>
            ,
            <Link className="underline underline-offset-2" href="#">
              隐私政策
            </Link>
            ,
            <Link className="underline underline-offset-2" href="#">
              AI 辅助判断免责声明
            </Link>
          </p>
        </footer>
      </div>
    </div>
  );
}
