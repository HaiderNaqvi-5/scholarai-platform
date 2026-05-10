import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Audit" };
export default function AdminAuditPage() {
  return (
    <PlaceholderRoute
      title="Role-change audit"
      blurb="Every role change with actor, timestamp, reason. Owner can revert from this page."
      sprint="Sprint 9"
    />
  );
}
