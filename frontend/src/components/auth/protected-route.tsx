"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";

export function ProtectedRoute({
  children,
  message = "Checking your workspace session.",
}: {
  children: React.ReactNode;
  message?: string;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const nextPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(nextPath)}`);
    }
  }, [isAuthenticated, isLoading, nextPath, router]);

  if (isLoading) {
    return (
      <main className="app-shell">
        <div className="page-shell">
          <section className="surface-card">
            <p className="section-eyebrow">Workspace access</p>
            <h1 className="page-title">Session check in progress.</h1>
            <p className="page-description">{message}</p>
          </section>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
