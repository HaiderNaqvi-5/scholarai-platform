import type { Metadata } from "next";
import { Suspense } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardShell } from "@/components/dashboard/dashboard-shell";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Your scholarship workspace — saved opportunities, profile status, and next steps.",
};

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <ProtectedRoute>
        <DashboardShell />
      </ProtectedRoute>
    </Suspense>
  );
}
