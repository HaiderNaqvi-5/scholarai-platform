"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";
import type { Role } from "@/lib/api";

const STUDENT_ROLES: Role[] = ["enduser_student", "student", "internal_user", "dev", "admin", "owner"];
const MENTOR_ROLES: Role[] = ["mentor", "admin", "owner"];
const ADMIN_ROLES: Role[] = ["admin", "owner"];
const OWNER_ROLES: Role[] = ["owner"];

export const ROLE_GROUPS = {
  student: STUDENT_ROLES,
  mentor: MENTOR_ROLES,
  admin: ADMIN_ROLES,
  owner: OWNER_ROLES,
} as const;

export type RoleGroup = keyof typeof ROLE_GROUPS;

export function hasRole(user: { role: Role } | null, group: RoleGroup): boolean {
  if (!user) return false;
  return ROLE_GROUPS[group].includes(user.role);
}

export function RoleGuard({
  group,
  children,
  fallback,
}: {
  group: RoleGroup;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.status === "guest") {
      const next = typeof window !== "undefined" ? window.location.pathname : "/";
      router.replace(`/login?next=${encodeURIComponent(next)}`);
    }
  }, [auth.status, router]);

  if (auth.status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center" aria-busy="true">
        <div className="size-8 animate-pulse rounded-full bg-paper-dim" />
      </div>
    );
  }
  if (auth.status === "guest") return null;
  if (!hasRole(auth.user, group)) {
    return (
      fallback ?? (
        <div className="mx-auto max-w-md p-8">
          <h1 className="font-display text-2xl">Not available</h1>
          <p className="mt-2 text-ink-muted">
            Your account doesn&apos;t have access to this area.
          </p>
        </div>
      )
    );
  }
  return <>{children}</>;
}
