"use client";

import { Suspense } from "react";
import { AdminRoute } from "@/components/auth/admin-route";
import { AnalyticsDashboardShell } from "@/components/admin/analytics-dashboard-shell";

export default function AdminPage() {
  return (
    <Suspense fallback={null}>
      <AdminRoute>
        <AnalyticsDashboardShell />
      </AdminRoute>
    </Suspense>
  );
}
