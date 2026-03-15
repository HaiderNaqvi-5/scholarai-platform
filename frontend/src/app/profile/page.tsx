import { ProtectedRoute } from "@/components/auth/protected-route";
import { ProfileFormShell } from "@/components/profile/profile-form-shell";

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileFormShell />
    </ProtectedRoute>
  );
}
