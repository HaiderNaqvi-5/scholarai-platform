import { ProtectedRoute } from "@/components/auth/protected-route";
import { DocumentAssistanceShell } from "@/components/documents/document-assistance-shell";

export default function DocumentFeedbackPage() {
  return (
    <ProtectedRoute>
      <DocumentAssistanceShell />
    </ProtectedRoute>
  );
}
