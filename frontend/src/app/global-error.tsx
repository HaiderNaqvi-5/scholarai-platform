"use client";

import Link from "next/link";

/**
 * global-error.tsx — Next 16 root error boundary. Fires only when
 * app/layout.tsx itself throws. Must include <html> and <body> because
 * the layout is bypassed.
 */
export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#FBF7EE",
          color: "#0E1A1F",
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          padding: "1.5rem",
        }}
      >
        <div style={{ maxWidth: 520, textAlign: "center" }}>
          <h1 style={{ fontSize: 32, fontStyle: "italic", margin: 0, lineHeight: 1.1 }}>
            AidwiseAI is unavailable right now.
          </h1>
          <p style={{ marginTop: 16, fontSize: 15, lineHeight: 1.6, color: "#4A5663" }}>
            We&rsquo;ve logged the error. Reload the page, or email{" "}
            <a href="mailto:support@aidwiseai.pk" style={{ color: "#1B3A6B" }}>
              support@aidwiseai.pk
            </a>
            .
          </p>
          {error.digest ? (
            <div style={{ marginTop: 12, fontFamily: "ui-monospace, monospace", fontSize: 13, color: "#6E7984" }}>
              Incident ID: <code>{error.digest}</code>
            </div>
          ) : null}
          <div style={{ marginTop: 28 }}>
            <Link
              href="/"
              style={{
                display: "inline-flex",
                height: 44,
                alignItems: "center",
                padding: "0 20px",
                background: "#0E1A1F",
                color: "#FFFDF9",
                borderRadius: 12,
                fontSize: 14,
                textDecoration: "none",
                fontWeight: 500,
              }}
            >
              Reload
            </Link>
          </div>
        </div>
      </body>
    </html>
  );
}
