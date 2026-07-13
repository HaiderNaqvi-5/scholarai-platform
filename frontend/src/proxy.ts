import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/login",
  "/signup",
  "/sso-callback",
  "/legal/(.*)",
  "/api/healthz",
  "/__clerk/(.*)",
]);

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

// Origin allowlist for request authorization. Blocks subdomain cookie-leak /
// CSRF (Clerk prod-deploy guidance). Comma-separated; blank = unrestricted
// (dev / back-compat — no behavior change until set in prod).
const authorizedParties = (process.env.NEXT_PUBLIC_APP_ORIGIN || "")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);

const passThrough = () => NextResponse.next();

export default clerkEnabled
  ? clerkMiddleware(
      async (auth, req) => {
        if (!isPublicRoute(req)) {
          await auth.protect();
        }
      },
      authorizedParties.length ? { authorizedParties } : undefined,
    )
  : passThrough;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/__clerk/(.*)",
    "/(api|trpc)(.*)",
  ],
};
