"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { SkeletonLine } from "@/components/ui/skeleton";
import { useAuth } from "@/components/auth/auth-provider";
import { Capability, hasAnyCapability } from "@/lib/authorization";

export function MentorRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { accessToken, currentUser, isAuthenticated, isLoading } = useAuth();
  const nextPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
  const hasMentorAccess = hasAnyCapability(currentUser, accessToken, [
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
  ]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
      return;
    }

    if (!isLoading && isAuthenticated && !hasMentorAccess) {
      router.replace("/dashboard");
    }
  }, [hasMentorAccess, isAuthenticated, isLoading, nextPath, router]);

  if (isLoading) {
    return (
      <main className="app-shell">
        <div className="page-shell">
          <section className="surface-card">
            <SkeletonLine count={2} />
          </section>
        </div>
      </main>
    );
  }

  if (!isAuthenticated || !hasMentorAccess) {
    return null;
  }

  return <>{children}</>;
}
