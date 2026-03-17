import type { Metadata } from "next";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ProfileFormShell } from "@/components/profile/profile-form-shell";

export const metadata: Metadata = {
  title: "Profile",
  description:
    "Review and update the profile fields used for scholarship recommendations.",
};

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileFormShell mode="profile" />
    </ProtectedRoute>
  );
}
