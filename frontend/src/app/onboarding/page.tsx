"use client";

import { AuthEntrance } from "@/components/auth/auth-entrance";
import { OnboardingFlow } from "@/components/onboarding/onboarding-flow";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function OnboardingPage() {
  return (
    <ProtectedRoute>
      <AuthEntrance 
        title="Personalize."
        subtitle="Let's build your matching engine profile."
      >
        <OnboardingFlow />
      </AuthEntrance>
    </ProtectedRoute>
  );
}
