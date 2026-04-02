import type { Metadata } from "next";
import { Suspense } from "react";

import { OwnerRoute } from "@/components/auth/owner-route";
import { OwnerDashboardShell } from "@/components/owner/owner-dashboard-shell";

export const metadata: Metadata = {
  title: "Owner Home",
  description:
    "Owner-only governance home for platform oversight, stage conformance visibility, and policy pathways.",
};

export default function OwnerPage() {
  return (
    <Suspense fallback={null}>
      <OwnerRoute>
        <OwnerDashboardShell />
      </OwnerRoute>
    </Suspense>
  );
}
