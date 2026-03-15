import { ProtectedRoute } from "@/components/auth/protected-route";
import { RecommendationWorkspace } from "@/components/recommendations/recommendation-workspace";

export default function RecommendationsPage() {
  return (
    <ProtectedRoute>
      <RecommendationWorkspace />
    </ProtectedRoute>
  );
}
