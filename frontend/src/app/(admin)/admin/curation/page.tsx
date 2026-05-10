import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Curation" };
export default function AdminCurationPage() {
  return (
    <PlaceholderRoute
      title="Curation queue"
      blurb="Records by state: raw, validated, published. Approve, reject, publish, unpublish — each with an audit note."
      sprint="Sprint 8"
    />
  );
}
