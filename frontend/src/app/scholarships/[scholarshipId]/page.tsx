import { ScholarshipDetailShell } from "@/components/scholarships/scholarship-detail-shell";

export default async function ScholarshipDetailPage({
  params,
}: {
  params: Promise<{ scholarshipId: string }>;
}) {
  const { scholarshipId } = await params;

  return <ScholarshipDetailShell scholarshipId={scholarshipId} />;
}
