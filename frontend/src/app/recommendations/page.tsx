import type { Metadata } from "next";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { RecommendationWorkspace } from "@/components/recommendations/recommendation-workspace";

export const metadata: Metadata = {
  title: "Recommendations",
  description:
    "Scholarships ranked by your profile with explanations of what matched and what to verify.",
};

export default function RecommendationsPage() {
  return (
    <ProtectedRoute>
      <RecommendationWorkspace />
    </ProtectedRoute>
  );
}
