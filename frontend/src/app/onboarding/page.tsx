import { ProtectedRoute } from "@/components/auth/protected-route";
import { ProfileFormShell } from "@/components/profile/profile-form-shell";

export default function OnboardingPage() {
  return (
    <ProtectedRoute>
      <ProfileFormShell />
    </ProtectedRoute>
  );
}
