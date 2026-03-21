"use client";

import { Suspense } from "react";
import { AdminRoute } from "@/components/auth/admin-route";
import { AnalyticsDashboardShell } from "@/components/admin/analytics-dashboard-shell";
import { SkeletonLine } from "@/components/ui/skeleton";

export default function AdminPage() {
  return (
    <Suspense
      fallback={
        <main className="app-shell">
          <div className="page-shell">
            <section className="surface-card">
              <SkeletonLine count={2} />
            </section>
          </div>
        </main>
      }
    >
      <AdminRoute>
        <AnalyticsDashboardShell />
      </AdminRoute>
    </Suspense>
  );
}
