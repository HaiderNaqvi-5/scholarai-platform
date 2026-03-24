"use client";

import type { ReactNode } from "react";
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
const ACCESS_TOKEN_EXPIRY_KEY = "scholarai.access_token_expires_at";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    typeof window !== "undefined"
      ? localStorage.getItem(ACCESS_TOKEN_KEY)
      : null,
  );
  const [refreshToken, setRefreshToken] = useState<string | null>(() =>
    typeof window !== "undefined"
      ? localStorage.getItem(REFRESH_TOKEN_KEY)
      : null,
  );
  const [currentUser, setCurrentUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(ACCESS_TOKEN_EXPIRY_KEY);
    setAccessToken(null);
    setRefreshToken(null);
    setCurrentUser(null);
  }, []);

  const loadCurrentUser = useCallback(async (token: string) => {
    const user = await apiRequest<UserSession>("/auth/me", { token });
    setCurrentUser(user);
  }, []);

  const persistTokens = useCallback((tokens: AuthTokens) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    localStorage.setItem(
      ACCESS_TOKEN_EXPIRY_KEY,
      String(Date.now() + tokens.expires_in * 1000),
    );
    setAccessToken(tokens.access_token);
    setRefreshToken(tokens.refresh_token);
  }, []);

  const refreshSession = useCallback(
    async (tokenOverride?: string | null) => {
      const refreshTokenToUse =
        tokenOverride ??
        refreshToken ??
        (typeof window !== "undefined"
          ? localStorage.getItem(REFRESH_TOKEN_KEY)
          : null);

      if (!refreshTokenToUse) {
        clearSession();
        throw new Error("No refresh token available");
      }

      const tokens = await apiRequest<AuthTokens>("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshTokenToUse }),
      });
      persistTokens(tokens);
      await loadCurrentUser(tokens.access_token);
      return tokens.access_token;
    },
    [clearSession, loadCurrentUser, persistTokens, refreshToken],
  );

  useEffect(() => {
    const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (!storedToken && !storedRefreshToken) {
      return;
    }

    const bootstrapSession = async () => {
      if (!storedToken && storedRefreshToken) {
        await refreshSession(storedRefreshToken);
        return;
      }

      await loadCurrentUser(storedToken as string);
    };

    bootstrapSession()
      .catch(async (error) => {
        if (isApiError(error) && error.status === 401 && storedRefreshToken) {
          try {
            await refreshSession(storedRefreshToken);
            return;
          } catch {
            clearSession();
            return;
          }
        }

        clearSession();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [
    clearSession,
    loadCurrentUser,
    refreshSession,
  ]);

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
    if (!accessToken && !refreshToken) {
      throw new Error("No active token");
    }
    try {
      if (!accessToken) {
        await refreshSession();
        return;
      }
      await loadCurrentUser(accessToken);
    } catch (error) {
      if (isApiError(error) && error.status === 401) {
        await refreshSession();
        return;
      }
      throw error;
    }
  }, [accessToken, loadCurrentUser, refreshSession, refreshToken]);

  useEffect(() => {
    const handleStorage = () => {
      const nextAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      const nextRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      setAccessToken(nextAccessToken);
      setRefreshToken(nextRefreshToken);

      if (!nextAccessToken) {
        setCurrentUser(null);
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => {
      window.removeEventListener("storage", handleStorage);
    };
  }, []);

  useEffect(() => {
    if (!refreshToken) {
      return;
    }

    const storedExpiry = localStorage.getItem(ACCESS_TOKEN_EXPIRY_KEY);
    if (!storedExpiry) {
      return;
    }

    const expiresAt = Number(storedExpiry);
    if (!Number.isFinite(expiresAt)) {
      return;
    }

    const refreshLeadMs = 60_000;
    const delay = Math.max(expiresAt - Date.now() - refreshLeadMs, 5_000);

    const timeoutId = window.setTimeout(() => {
      void refreshSession().catch(() => {
        clearSession();
      });
    }, delay);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [clearSession, refreshSession, refreshToken]);

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
