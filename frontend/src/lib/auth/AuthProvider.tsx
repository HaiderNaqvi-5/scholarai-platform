"use client";

/**
 * AuthProvider — dual-mode shell.
 *
 * - LocalAuthProvider: legacy path. Backend `/auth/login` issues an HS256
 *   JWT; tokens are stored in localStorage; `subscribeTokens` listens for
 *   cross-tab logout. This is the v1 codebase behaviour, preserved verbatim.
 *
 * - ClerkBackedAuthProvider: clerk mode (enabled when
 *   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set at build time). Observes the
 *   Clerk session via @clerk/nextjs hooks; on every isSignedIn change,
 *   fetches backend `/me` to populate the local `User` row. `login` and
 *   `signup` throw if called — the only callers (/login + /signup pages)
 *   branch on `clerkEnabled` and use the page-level useClerkLoginFlow /
 *   useClerkSignupFlow hooks directly. `logout` delegates to Clerk signOut.
 *
 * The two implementations live in separate components so each one's
 * effects + state machines stay isolated. The outer dispatcher picks the
 * right one at module load time — env var is fixed for the lifetime of
 * the process.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { useAuth as useClerkAuth } from "@clerk/nextjs";
import { endpoints, getTokens, setTokens, subscribeTokens, type User } from "@/lib/api";
import { clerkEnabled, useClerkLogout } from "./clerkAdapter";

type AuthState =
  | { status: "loading"; user: null }
  | { status: "guest"; user: null }
  | { status: "authed"; user: User };

type SignupInput = Parameters<typeof endpoints.auth.register>[0];

type AuthContextValue = AuthState & {
  login: (input: { email: string; password: string }) => Promise<User>;
  signup: (input: SignupInput) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  if (clerkEnabled) return <ClerkBackedAuthProvider>{children}</ClerkBackedAuthProvider>;
  return <LocalAuthProvider>{children}</LocalAuthProvider>;
}

function LocalAuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading", user: null });
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    const tokens = getTokens();
    if (!tokens?.access) {
      setState({ status: "guest", user: null });
      return null;
    }
    try {
      const user = await endpoints.auth.me();
      setState({ status: "authed", user });
      return user;
    } catch {
      setTokens(null);
      setState({ status: "guest", user: null });
      return null;
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshUser();
    const unsub = subscribeTokens((t) => {
      if (!t) setState({ status: "guest", user: null });
    });
    return () => {
      unsub();
    };
  }, [refreshUser]);

  const login = useCallback<AuthContextValue["login"]>(async (input) => {
    const tokenRes = await endpoints.auth.login(input);
    setTokens({
      access: tokenRes.access_token,
      refresh: tokenRes.refresh_token,
      expiresAt: Date.now() + tokenRes.expires_in * 1000,
    });
    const user = await endpoints.auth.me();
    setState({ status: "authed", user });
    return user;
  }, []);

  const signup = useCallback<AuthContextValue["signup"]>(async (input) => {
    await endpoints.auth.register(input);
    return login({ email: input.email, password: input.password });
  }, [login]);

  const logout = useCallback(async () => {
    try {
      await endpoints.auth.logout();
    } catch {
      // ignore — token revoke best-effort
    }
    setTokens(null);
    setState({ status: "guest", user: null });
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, signup, logout, refreshUser }),
    [state, login, signup, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function ClerkBackedAuthProvider({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn, userId } = useClerkAuth();
  const clerkSignOut = useClerkLogout();
  const router = useRouter();
  const [state, setState] = useState<AuthState>({ status: "loading", user: null });

  const refreshUser = useCallback(async () => {
    if (!isLoaded) return null;
    if (!isSignedIn) {
      setState({ status: "guest", user: null });
      return null;
    }
    try {
      const user = await endpoints.auth.me();
      setState({ status: "authed", user });
      return user;
    } catch {
      setState({ status: "guest", user: null });
      return null;
    }
  }, [isLoaded, isSignedIn]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshUser();
  }, [refreshUser, userId]);

  const login = useCallback<AuthContextValue["login"]>(async () => {
    throw new Error(
      "AuthProvider.login is not callable in clerk mode — use useClerkLoginFlow() from clerkAdapter on the page.",
    );
  }, []);

  const signup = useCallback<AuthContextValue["signup"]>(async () => {
    throw new Error(
      "AuthProvider.signup is not callable in clerk mode — use useClerkSignupFlow() from clerkAdapter on the page.",
    );
  }, []);

  const logout = useCallback(async () => {
    await clerkSignOut();
    setTokens(null);
    setState({ status: "guest", user: null });
    router.replace("/login");
  }, [clerkSignOut, router]);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, signup, logout, refreshUser }),
    [state, login, signup, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
