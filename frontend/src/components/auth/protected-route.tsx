"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";

export function ProtectedRoute({
  children,
  message = "Checking your workspace session.",
}: {
  children: React.ReactNode;
  message?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [isAuthenticated, isLoading, pathname, router]);

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
