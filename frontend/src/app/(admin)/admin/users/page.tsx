import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Users" };
export default function AdminUsersPage() {
  return (
    <PlaceholderRoute
      title="Users"
      blurb="Roster, current role, last activity. Owner-only role changes with reason capture."
      sprint="Sprint 9"
    />
  );
}
