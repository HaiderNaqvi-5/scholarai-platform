import { ProtectedRoute } from "@/components/auth/protected-route";
import { InterviewPracticeShell } from "@/components/interview/interview-practice-shell";

export default function InterviewPage() {
  return (
    <ProtectedRoute>
      <InterviewPracticeShell />
    </ProtectedRoute>
  );
}
