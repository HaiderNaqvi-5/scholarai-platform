"use client";

import { MentorRoute } from "@/components/auth/mentor-route";
import { MentorDashboardShell } from "@/components/mentor/mentor-dashboard-shell";

export default function MentorPage() {
  return (
    <MentorRoute>
      <MentorDashboardShell />
    </MentorRoute>
  );
}
