"use client";

/**
 * Clerk → existing auth surface adapter.
 *
 * Three hooks wrap @clerk/nextjs' sign-in / sign-up / sign-out flows and
 * map Clerk's `ClerkAPIError` shape onto the repo's `ApiError` so that
 * the existing /login + /signup pages can show the same sindoor-bordered
 * error envelope they show for backend errors.
 *
 * Hooks must be called inside React components that are descendants of
 * <ClerkProvider> (i.e. clerk-mode only). The login + signup pages branch
 * on `clerkEnabled` and only mount these hooks when the env var is set.
 */

import { useSignIn, useSignUp, useClerk } from "@clerk/nextjs";
import { ApiError } from "@/lib/api";

type ClerkErrorEntry = { code: string; message: string; longMessage?: string };

function mapClerkError(err: unknown): ApiError {
  if (typeof err === "object" && err !== null && "errors" in err) {
    const arr = (err as { errors?: ClerkErrorEntry[] }).errors;
    const first = arr && arr.length > 0 ? arr[0] : undefined;
    const code = first?.code ?? "CLERK_ERROR";
    const message = first?.longMessage ?? first?.message ?? "Authentication error";
    const status =
      code === "form_password_incorrect" || code === "form_identifier_not_found"
        ? 401
        : code === "form_identifier_exists"
          ? 409
          : code === "form_code_incorrect" || code === "verification_failed"
            ? 422
            : code.startsWith("form_")
              ? 422
              : 400;
    return new ApiError(status, code, message);
  }
  if (err instanceof ApiError) return err;
  return new ApiError(
    500,
    "CLERK_ERROR",
    err instanceof Error ? err.message : "Unknown auth error",
  );
}

export function useClerkLoginFlow() {
  const { signIn, setActive, isLoaded } = useSignIn();
  return async ({ email, password }: { email: string; password: string }) => {
    if (!isLoaded || !signIn || !setActive) {
      throw new ApiError(503, "CLERK_NOT_READY", "Sign-in is still loading. Try again in a moment.");
    }
    try {
      const attempt = await signIn.create({ identifier: email, password });
      if (attempt.status === "complete") {
        await setActive({ session: attempt.createdSessionId });
        return;
      }
      throw new ApiError(
        400,
        "VERIFICATION_REQUIRED",
        "Additional verification required — open the Clerk dashboard to inspect this account.",
      );
    } catch (err) {
      throw mapClerkError(err);
    }
  };
}

export function useClerkSignupFlow() {
  const { signUp, setActive, isLoaded } = useSignUp();
  const create = async (input: { email: string; password: string; fullName: string }) => {
    if (!isLoaded || !signUp) {
      throw new ApiError(503, "CLERK_NOT_READY", "Sign-up is still loading. Try again in a moment.");
    }
    const trimmed = input.fullName.trim();
    const [first, ...rest] = trimmed.split(/\s+/);
    try {
      await signUp.create({
        emailAddress: input.email,
        password: input.password,
        firstName: first || undefined,
        lastName: rest.length > 0 ? rest.join(" ") : undefined,
      });
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
    } catch (err) {
      throw mapClerkError(err);
    }
  };
  const verifyCode = async (code: string) => {
    if (!isLoaded || !signUp || !setActive) {
      throw new ApiError(503, "CLERK_NOT_READY", "Verification is still loading. Try again in a moment.");
    }
    try {
      const result = await signUp.attemptEmailAddressVerification({ code });
      if (result.status === "complete") {
        await setActive({ session: result.createdSessionId });
        return;
      }
      throw new ApiError(422, "VERIFICATION_INCOMPLETE", "Verification did not complete. Re-enter the code.");
    } catch (err) {
      throw mapClerkError(err);
    }
  };
  const resend = async () => {
    if (!isLoaded || !signUp) {
      throw new ApiError(503, "CLERK_NOT_READY", "Resend is still loading. Try again in a moment.");
    }
    try {
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
    } catch (err) {
      throw mapClerkError(err);
    }
  };
  return { create, verifyCode, resend, isLoaded };
}

export function useClerkLogout() {
  const { signOut } = useClerk();
  return async () => {
    await signOut();
  };
}

/** True when the Clerk publishable key is set at build time. */
export const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
