import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Mentor review" };
export default function MentorDocumentPage() {
  return (
    <PlaceholderRoute
      title="Review document"
      blurb="Split view. Original draft and AI feedback on the left, structured form on the right: summary, strengths, revision priorities, caution notes."
      sprint="Sprint 7"
    />
  );
}
