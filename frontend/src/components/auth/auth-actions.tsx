"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { Capability, hasAnyCapability, hasCapability } from "@/lib/authorization";

export function AuthActions() {
  const router = useRouter();
  const { accessToken, currentUser, isAuthenticated, isLoading, logout } = useAuth();
  const canSeeCuration = hasCapability(
    currentUser,
    accessToken,
    Capability.CurationQueueRead,
  );
  const canSeeAdmin = hasAnyCapability(currentUser, accessToken, [
    Capability.AdminAuditRead,
    Capability.OwnerSystemRead,
  ]);
  const canSeeOwner = hasCapability(
    currentUser,
    accessToken,
    Capability.OwnerSystemRead,
  );

  if (isLoading) {
    return <div className="auth-actions auth-actions--loading" />;
  }

  if (!isAuthenticated) {
    return (
      <div className="auth-actions">
        <Link className="nav-link nav-link--quiet" href="/login">
          Sign in
        </Link>
        <Link className="auth-link auth-link--primary" href="/signup">
          Create account
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-actions">
      <div className="auth-chip">
        <span className="auth-chip__label">Signed in</span>
        <strong>{currentUser?.full_name ?? "GrantPath AI user"}</strong>
      </div>
      <Link className="nav-link nav-link--quiet" href="/dashboard">
        Dashboard
      </Link>
      {canSeeCuration ? (
        <Link className="nav-link nav-link--quiet" href="/curation">
          Curation
        </Link>
      ) : null}
      {canSeeAdmin ? (
        <Link className="nav-link nav-link--quiet" href="/admin">
          Admin
        </Link>
      ) : null}
      {canSeeOwner ? (
        <Link className="nav-link nav-link--quiet" href="/owner">
          Owner
        </Link>
      ) : null}
      <button
        className="auth-link auth-link--secondary"
        onClick={() => {
          logout();
          router.push("/login");
        }}
        type="button"
      >
        Sign out
      </button>
    </div>
  );
}
