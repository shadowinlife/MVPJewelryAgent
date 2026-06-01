import { redirect } from "next/navigation";

import { isAdminAuthenticated } from "@/lib/auth";
import { AdminSidebar } from "@/components/admin/admin-sidebar";
import { MockModeFloater } from "@/components/layout/mock-mode-floater";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const isAdmin = await isAdminAuthenticated();
  if (!isAdmin) {
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar />
      <main className="flex-1 p-6 md:p-10">{children}</main>
      <MockModeFloater />
    </div>
  );
}
