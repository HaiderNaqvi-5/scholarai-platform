import type { Metadata } from "next";
import { Suspense } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ProfileFormShell } from "@/components/profile/profile-form-shell";

export const metadata: Metadata = {
  title: "Onboarding",
  description:
    "Set up your profile in under a minute to get personalized scholarship recommendations.",
};

export default function OnboardingPage() {
  return (
    <Suspense fallback={null}>
      <ProtectedRoute>
        <ProfileFormShell mode="onboarding" />
      </ProtectedRoute>
    </Suspense>
  );
}
