"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { SkeletonLine } from "@/components/ui/skeleton";
import { Capability, hasCapability } from "@/lib/authorization";

export function OwnerRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { accessToken, currentUser, isAuthenticated, isLoading } = useAuth();
  const nextPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
  const hasOwnerAccess = hasCapability(
    currentUser,
    accessToken,
    Capability.OwnerSystemRead,
  );

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
      return;
    }

    if (!isLoading && isAuthenticated && !hasOwnerAccess) {
      router.replace("/dashboard");
    }
  }, [hasOwnerAccess, isAuthenticated, isLoading, nextPath, router]);

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

  if (!isAuthenticated || !hasOwnerAccess) {
    return null;
  }

  return <>{children}</>;
}
