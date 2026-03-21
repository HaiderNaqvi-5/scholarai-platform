import type { Metadata } from "next";
import { Suspense } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ProfileFormShell } from "@/components/profile/profile-form-shell";

export const metadata: Metadata = {
  title: "Profile",
  description:
    "Review and update the profile fields used for scholarship recommendations.",
};

export default function ProfilePage() {
  return (
    <Suspense fallback={null}>
      <ProtectedRoute>
        <ProfileFormShell mode="profile" />
      </ProtectedRoute>
    </Suspense>
  );
}
