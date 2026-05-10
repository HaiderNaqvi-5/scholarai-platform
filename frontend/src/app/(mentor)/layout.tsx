import { AppShell } from "@/components/shell/AppShell";
import { RoleGuard } from "@/lib/auth/RoleGuard";

export default function MentorLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard group="mentor">
      <AppShell>{children}</AppShell>
    </RoleGuard>
  );
}
