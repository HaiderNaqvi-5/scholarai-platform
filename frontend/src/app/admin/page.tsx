"use client";

import { Suspense } from "react";

import { AdminAuditRoute } from "@/components/auth/admin-audit-route";
import { AnalyticsDashboardShell } from "@/components/admin/analytics-dashboard-shell";
import { SkeletonLine } from "@/components/ui/skeleton";

function AdminPageFallback() {
  return (
    <main className="app-shell">
      <div className="page-shell">
        <section className="surface-card">
          <SkeletonLine count={2} />
        </section>
      </div>
    </main>
  );
}

export default function AdminPage() {
  return (
    <Suspense fallback={<AdminPageFallback />}>
      <AdminAuditRoute>
        <AnalyticsDashboardShell />
      </AdminAuditRoute>
    </Suspense>
  );
}
