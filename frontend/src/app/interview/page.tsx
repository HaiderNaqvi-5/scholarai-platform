import type { Metadata } from "next";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { InterviewPracticeShell } from "@/components/interview/interview-practice-shell";

export const metadata: Metadata = {
  title: "Interview Practice",
  description:
    "Practice scholarship interview answers with rubric-based scoring on clarity, relevance, and specificity.",
};

export default function InterviewPage() {
  return (
    <ProtectedRoute>
      <InterviewPracticeShell />
    </ProtectedRoute>
  );
}
