import { AppShell } from "@/components/shell/AppShell";
import { RoleGuard } from "@/lib/auth/RoleGuard";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard group="admin">
      <AppShell>{children}</AppShell>
    </RoleGuard>
  );
}
