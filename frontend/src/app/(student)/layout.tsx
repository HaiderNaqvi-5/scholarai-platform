import { AppShell } from "@/components/shell/AppShell";
import { RoleGuard } from "@/lib/auth/RoleGuard";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard group="student">
      <AppShell>{children}</AppShell>
    </RoleGuard>
  );
}
