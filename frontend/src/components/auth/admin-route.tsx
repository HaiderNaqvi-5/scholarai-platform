"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";

export function AdminRoute({
  children,
  message = "Checking curator access.",
}: {
  children: React.ReactNode;
  message?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { currentUser, isAuthenticated, isLoading } = useAuth();
  const nextPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
      return;
    }

    if (!isLoading && isAuthenticated && currentUser?.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [currentUser?.role, isAuthenticated, isLoading, nextPath, router]);

  if (isLoading) {
    return (
      <main className="app-shell">
        <div className="page-shell">
          <section className="surface-card">
            <p className="section-eyebrow">Curator access</p>
            <h1 className="page-title">Access check in progress.</h1>
            <p className="page-description">{message}</p>
          </section>
        </div>
      </main>
    );
  }

  if (!isAuthenticated || currentUser?.role !== "admin") {
    return null;
  }

  return <>{children}</>;
}
