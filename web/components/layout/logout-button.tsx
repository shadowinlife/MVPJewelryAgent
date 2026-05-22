"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";

export function LogoutButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [loading, setLoading] = useState(false);

  async function handleLogout() {
    setLoading(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      startTransition(() => {
        router.replace("/login");
        router.refresh();
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      size="sm"
      variant="ghost"
      type="button"
      onClick={handleLogout}
      disabled={loading || pending}
      className="cursor-pointer text-xs text-muted-foreground hover:text-foreground"
    >
      <LogOut className="mr-1 h-3.5 w-3.5" aria-hidden />
      {loading || pending ? "退出中…" : "退出"}
    </Button>
  );
}
