import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Admin" };
export default function AdminOverviewPage() {
  return (
    <PlaceholderRoute
      title="Admin overview"
      blurb="Platform analytics: users, scholarships, documents, interview sessions, ingestion run health. KPI alerts polled every 60s from /health."
      sprint="Sprint 9"
    />
  );
}
