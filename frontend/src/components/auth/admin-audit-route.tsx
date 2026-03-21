"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { SkeletonLine } from "@/components/ui/skeleton";
import { Capability, hasAnyCapability } from "@/lib/authorization";

export function AdminAuditRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { accessToken, currentUser, isAuthenticated, isLoading } = useAuth();
  const nextPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
  const hasAdminAnalyticsAccess = hasAnyCapability(currentUser, accessToken, [
    Capability.AdminAuditRead,
    Capability.OwnerSystemRead,
  ]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
      return;
    }

    if (!isLoading && isAuthenticated && !hasAdminAnalyticsAccess) {
      router.replace("/dashboard");
    }
  }, [hasAdminAnalyticsAccess, isAuthenticated, isLoading, nextPath, router]);

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

  if (!isAuthenticated || !hasAdminAnalyticsAccess) {
    return null;
  }

  return <>{children}</>;
}
