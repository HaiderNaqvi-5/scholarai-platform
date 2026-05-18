"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { endpoints, getTokens, setTokens, subscribeTokens, type User } from "@/lib/api";

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

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
