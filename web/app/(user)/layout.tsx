import { redirect } from "next/navigation";

import { MobileBottomNav } from "@/components/yaoqi";
import { TopNav } from "@/components/layout/top-nav";
import { MockModeFloater } from "@/components/layout/mock-mode-floater";
import { getCurrentUser } from "@/lib/auth";

export default async function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-12">
      <TopNav user={user} />
      <main className="mx-auto w-full max-w-6xl px-4 py-6 md:px-6 md:py-10">
        {children}
      </main>
      <MobileBottomNav />
      <MockModeFloater />
    </div>
  );
}
