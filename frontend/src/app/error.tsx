"use client";

import { useEffect } from "react";
import { SystemErrorLayout } from "@/components/system/SystemErrorLayout";

/**
 * Route-segment error boundary (Front-upgrade §6.33). The global root
 * boundary is in app/global-error.tsx and only fires when the layout itself
 * crashes; this one handles per-route render errors.
 */
export default function RouteError({
  error,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (typeof window !== "undefined") {
      console.error("[system.500]", error.message, error.digest);
    }
  }, [error]);

  return (
    <SystemErrorLayout
      title="Something went wrong on our side."
      description="We've logged the error. Try again, or email support@aidwiseai.pk."
      primary={{ href: "/", label: "Try again" }}
      secondary={{ label: "Email support", mailto: "support@aidwiseai.pk" }}
      meta={
        error.digest ? (
          <span>
            Incident ID: <code>{error.digest}</code>
          </span>
        ) : undefined
      }
    />
  );
}
