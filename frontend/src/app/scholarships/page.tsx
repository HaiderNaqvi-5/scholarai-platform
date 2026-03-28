import { Suspense } from "react";

import type { Metadata } from "next";

import { ScholarshipBrowseShell } from "@/components/scholarships/scholarship-browse-shell";

export const metadata: Metadata = {
  title: "Scholarships",
  description:
    "Browse a curated catalog of published scholarships with structured filters and verified deadlines.",
};

export default function ScholarshipsPage() {
  return (
    <Suspense fallback={null}>
      <ScholarshipBrowseShell />
    </Suspense>
  );
}
