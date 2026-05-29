import type { NextConfig } from "next";

/**
 * Security headers on every response (S2).
 *
 * Backend `SecurityHeadersMiddleware` covers the API surface; this block
 * does the same for the Next.js SSR / static surface so the browser sees
 * a coherent policy across both origins.
 *
 * CSP intentionally allows the API origin for `connect-src` and inline
 * styles for Tailwind 4's atomic CSS (`unsafe-inline` is required because
 * Tailwind ships generated `<style>` blocks; tightening to nonces would
 * require a custom App Router renderer).
 */
const apiOrigin = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"
).replace(/\/api\/v\d+\/?$/, "");

const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  `connect-src 'self' ${apiOrigin} https://*.clerk.accounts.dev https://clerk-telemetry.com`,
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  // Tailwind 4 + Next.js inline runtime styles
  "style-src 'self' 'unsafe-inline'",
  "frame-src https://challenges.cloudflare.com https://*.clerk.accounts.dev",
  // Clerk SDK spawns Web Workers from blob: URIs for telemetry + CAPTCHA.
  // Without an explicit worker-src, browsers fall back to script-src which
  // does not include blob: → workers blocked + console errors.
  "worker-src 'self' blob:",
  // Next.js dev mode injects eval()-using HMR shim; tighten in prod build
  process.env.NODE_ENV === "production"
    ? "script-src 'self' 'unsafe-inline' https://*.clerk.accounts.dev https://challenges.cloudflare.com"
    : "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.clerk.accounts.dev https://challenges.cloudflare.com",
].join("; ");

const SECURITY_HEADERS = [
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  },
  { key: "Content-Security-Policy", value: csp },
];

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: SECURITY_HEADERS,
      },
    ];
  },
};

export default nextConfig;
