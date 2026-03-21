"use client";

import { Suspense } from "react";

import { MentorRoute } from "@/components/auth/mentor-route";
import { MentorDashboardShell } from "@/components/mentor/mentor-dashboard-shell";

export default function MentorPage() {
  return (
    <Suspense fallback={null}>
      <MentorRoute>
        <MentorDashboardShell />
      </MentorRoute>
    </Suspense>
  );
}
