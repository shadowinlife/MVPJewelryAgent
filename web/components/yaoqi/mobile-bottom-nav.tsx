"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, FilePlus2, FolderOpen, User } from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  { key: "home", label: "首页", href: "/dashboard", icon: Home },
  { key: "new", label: "新建", href: "/cases/new", icon: FilePlus2 },
  { key: "cases", label: "案例", href: "/cases", icon: FolderOpen },
  { key: "me", label: "我的", href: "/me", icon: User },
] as const;

export function MobileBottomNav({ className }: { className?: string }) {
  const pathname = usePathname() ?? "";

  return (
    <nav
      aria-label="主导航"
      className={cn(
        "fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden",
        "pb-[env(safe-area-inset-bottom)]",
        className,
      )}
    >
      <ul className="mx-auto grid max-w-md grid-cols-4">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <li key={item.key}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex h-14 flex-col items-center justify-center gap-0.5 text-[11px] transition-colors",
                  active
                    ? "text-[var(--color-gold-antique)]"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5",
                    active ? "stroke-[2.2]" : "stroke-[1.6]",
                  )}
                  aria-hidden
                />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
