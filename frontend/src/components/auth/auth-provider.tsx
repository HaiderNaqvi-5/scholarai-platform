"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { apiRequest } from "@/lib/api";
import type { ApiError, AuthTokens, UserSession } from "@/lib/types";

const ACCESS_TOKEN_KEY = "scholarai.access_token";
const REFRESH_TOKEN_KEY = "scholarai.refresh_token";

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = LoginPayload & {
  full_name: string;
};

type AuthContextValue = {
  accessToken: string | null;
  currentUser: UserSession | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    setAccessToken(null);
    setCurrentUser(null);
  }, []);

  const loadCurrentUser = useCallback(async (token: string) => {
    const user = await apiRequest<UserSession>("/auth/me", { token });
    setCurrentUser(user);
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    setAccessToken(storedToken);
    loadCurrentUser(storedToken)
      .catch(() => {
        clearSession();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [clearSession, loadCurrentUser]);

  const persistTokens = useCallback((tokens: AuthTokens) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    setAccessToken(tokens.access_token);
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const tokens = await apiRequest<AuthTokens>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: payload.email.toLowerCase(),
          password: payload.password,
        }),
      });
      persistTokens(tokens);
      try {
        await loadCurrentUser(tokens.access_token);
      } catch (error) {
        clearSession();
        throw error;
      }
    },
    [clearSession, loadCurrentUser, persistTokens],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await apiRequest<UserSession>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: payload.email.toLowerCase(),
          password: payload.password,
          full_name: payload.full_name,
        }),
      });
      await login(payload);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const refreshUser = useCallback(async () => {
    if (!accessToken) {
      throw new Error("No active token");
    }
    await loadCurrentUser(accessToken);
  }, [accessToken, loadCurrentUser]);

  const value = useMemo(
    () => ({
      accessToken,
      currentUser,
      isLoading,
      isAuthenticated: Boolean(accessToken && currentUser),
      login,
      register,
      logout,
      refreshUser,
    }),
    [accessToken, currentUser, isLoading, login, logout, refreshUser, register],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    "status" in error
  );
}
