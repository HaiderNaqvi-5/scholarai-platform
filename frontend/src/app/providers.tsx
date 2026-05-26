"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { AuthProvider } from "@/lib/auth/AuthProvider";
import { CookieBanner } from "@/components/consent/CookieBanner";
import { ConsentBar } from "@/components/consent/ConsentBar";
import { OfflineBanner } from "@/components/system/OfflineBanner";

const CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

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

  const inner = (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
      <OfflineBanner />
      <CookieBanner />
      <ConsentBar />
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

  return CLERK_PUBLISHABLE_KEY ? (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} appearance={{ baseTheme: dark }}>
      {inner}
    </ClerkProvider>
  ) : (
    inner
  );
}
