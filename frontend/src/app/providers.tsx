"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";
import { AuthProvider } from "@/lib/auth/AuthProvider";
import { CookieBanner } from "@/components/consent/CookieBanner";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: (failureCount, err) => {
              const status = (err as { status?: number })?.status;
              if (status && status >= 400 && status < 500) return false;
              return failureCount < 2;
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
      <CookieBanner />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "var(--color-paper-white)",
            color: "var(--color-ink-deep)",
            border: "1px solid var(--color-border)",
            borderRadius: "12px",
            fontFamily: "var(--font-ui), sans-serif",
            fontSize: "13px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
