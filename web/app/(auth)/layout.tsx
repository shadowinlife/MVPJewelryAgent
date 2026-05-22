import { redirect } from "next/navigation";

import { MockModeFloater } from "@/components/layout/mock-mode-floater";
import { hasUserCookie } from "@/lib/auth";

export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // 只在真实 cookie 存在时跳走,避免 mock auto-login 兜底导致 /login 不可见。
  if (await hasUserCookie()) {
    redirect("/dashboard");
  }

  return (
    <div className="relative min-h-screen bg-background">
      {children}
      <MockModeFloater />
    </div>
  );
}
