import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse, type NextRequest } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/login",
  "/signup",
  "/legal/(.*)",
  "/api/healthz",
  "/booth/(.*)",
]);

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

const passThrough = (_req: NextRequest) => NextResponse.next();

export default clerkEnabled
  ? clerkMiddleware(async (auth, req) => {
      if (!isPublicRoute(req)) {
        await auth.protect();
      }
    })
  : passThrough;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js|jpg|jpeg|png|svg|gif|ico|webp|woff2?|ttf|otf|map)).*)",
  ],
};
