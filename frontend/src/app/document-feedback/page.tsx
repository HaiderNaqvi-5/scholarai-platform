import type { Metadata } from "next";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DocumentAssistanceShell } from "@/components/documents/document-assistance-shell";

export const metadata: Metadata = {
  title: "Documents",
  description:
    "Get structured feedback on statement of purpose and essay drafts for scholarship applications.",
};

export default function DocumentFeedbackPage() {
  return (
    <ProtectedRoute>
      <DocumentAssistanceShell />
    </ProtectedRoute>
  );
}
