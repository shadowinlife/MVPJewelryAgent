"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bot, Users, FolderOpen } from "lucide-react";

const navItems = [
  { label: "工作台", href: "/admin", icon: LayoutDashboard },
  { label: "LLM 配置", href: "/admin/llm-config", icon: Bot },
  { label: "用户管理", href: "/admin/users", icon: Users },
  { label: "案例管理", href: "/admin/cases", icon: FolderOpen },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 shrink-0 border-r md:block bg-[var(--sidebar)] text-[var(--sidebar-foreground)]">
      <div className="flex h-14 items-center border-b px-5">
        <span className="text-lg font-semibold text-[var(--sidebar-primary)]">
          曜齐 Admin
        </span>
      </div>
      <nav className="flex flex-col gap-1 p-3">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/admin" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)] font-medium"
                  : "hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
