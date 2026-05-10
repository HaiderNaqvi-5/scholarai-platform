import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";

export const metadata = { title: "Saved" };

export default function SavedPage() {
  return (
    <PlaceholderRoute
      title="Saved scholarships"
      blurb="Kanban tracker: saved → in progress → applied → closed. Drag to move. Optimistic updates, rollback on failure."
      sprint="Sprint 3"
    />
  );
}
