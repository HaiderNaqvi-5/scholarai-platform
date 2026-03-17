"use client";

import { AdminRoute } from "@/components/auth/admin-route";
import { AnalyticsDashboardShell } from "@/components/admin/analytics-dashboard-shell";

export default function AdminPage() {
  return (
    <AdminRoute>
      <AnalyticsDashboardShell />
    </AdminRoute>
  );
}
