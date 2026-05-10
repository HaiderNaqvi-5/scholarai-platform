import { PlaceholderRoute } from "@/components/shell/PlaceholderRoute";

export const metadata = { title: "New document" };

export default function NewDocumentPage() {
  return (
    <PlaceholderRoute
      title="Submit a document"
      blurb="Paste your draft or upload a file. Optional: ground feedback against one or more scholarships. Autosaves to local storage every 5 seconds."
      sprint="Sprint 5"
    />
  );
}
