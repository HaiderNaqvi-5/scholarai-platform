import { Suspense } from "react";

import { ScholarshipDetailShell } from "@/components/scholarships/scholarship-detail-shell";

export default async function ScholarshipDetailPage({
  params,
}: {
  params: Promise<{ scholarshipId: string }>;
}) {
  const { scholarshipId } = await params;

  return (
    <Suspense fallback={null}>
      <ScholarshipDetailShell scholarshipId={scholarshipId} />
    </Suspense>
  );
}
