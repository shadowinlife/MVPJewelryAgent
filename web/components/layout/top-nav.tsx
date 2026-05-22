import Link from "next/link";

import { BrandLogo } from "@/components/yaoqi";
import type { User } from "@/lib/types/domain";
import { tierLabel } from "@/lib/membership";
import { cn } from "@/lib/utils";

import { LogoutButton } from "./logout-button";

const items = [
  { label: "工作台", href: "/dashboard" },
  { label: "新建案例", href: "/cases/new" },
  { label: "案例库", href: "/cases" },
  { label: "会员", href: "/membership" },
  { label: "我的", href: "/me" },
] as const;

export function TopNav({ user }: { user: User }) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/85 backdrop-blur supports-backdrop-filter:bg-background/70">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 md:px-6">
        <Link href="/dashboard" aria-label="返回工作台">
          <BrandLogo size="sm" />
        </Link>

        <nav aria-label="桌面导航" className="hidden md:block">
          <ul className="flex items-center gap-1 text-sm">
            {items.map((it) => (
              <li key={it.href}>
                <Link
                  href={it.href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-foreground/80",
                    "hover:text-foreground hover:bg-card transition-colors",
                  )}
                >
                  {it.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden flex-col items-end leading-tight sm:flex">
            <span className="text-xs text-muted-foreground">{user.nickname}</span>
            <span className="text-[11px] tracking-wide text-gold-antique">
              {tierLabel(user.membership)}
            </span>
          </div>
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
