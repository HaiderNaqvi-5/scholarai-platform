import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";
export const metadata = { title: "Review queue" };
export default function MentorQueuePage() {
  return (
    <PlaceholderRoute
      title="Pending student documents"
      blurb="Documents waiting for human review. Click in to annotate. Submitted feedback is labeled as reviewed by a human mentor."
      sprint="Sprint 7"
    />
  );
}
