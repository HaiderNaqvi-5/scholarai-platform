import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Ingestion" };
export default function AdminIngestionPage() {
  return (
    <PlaceholderRoute
      title="Ingestion runs"
      blurb="Start runs, retry failures, bulk-retry, view captured HTML snapshots, assign to review queues."
      sprint="Sprint 8"
    />
  );
}
