import type { Metadata } from "next";
import { Suspense } from "react";

import { AdminRoute } from "@/components/auth/admin-route";
import { CurationDashboardShell } from "@/components/curation/curation-dashboard-shell";

export const metadata: Metadata = {
  title: "Curation",
  description:
    "Admin workspace for reviewing, validating, and publishing scholarship records.",
};

export default function CurationPage() {
  return (
    <Suspense fallback={null}>
      <AdminRoute>
        <CurationDashboardShell />
      </AdminRoute>
    </Suspense>
  );
}
