import { AdminRoute } from "@/components/auth/admin-route";
import { CurationDashboardShell } from "@/components/curation/curation-dashboard-shell";

export default function CurationPage() {
  return (
    <AdminRoute>
      <CurationDashboardShell />
    </AdminRoute>
  );
}
