import { Suspense } from "react";

import type { Metadata } from "next";

import { ScholarshipCompareShell } from "@/components/scholarships/scholarship-compare-shell";

export const metadata: Metadata = {
  title: "Compare Scholarships",
  description:
    "Compare selected scholarships side by side across deadline, funding, eligibility, and source fields.",
};

export default function ScholarshipComparePage() {
  return (
    <Suspense fallback={null}>
      <ScholarshipCompareShell />
    </Suspense>
  );
}
