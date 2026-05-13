import { api } from "../client";
import type { TokenResponse, User } from "../types";

export const auth = {
  register: (input: { email: string; password: string; full_name?: string }) =>
    api.post<User>("/auth/register", input, { auth: false }),

  login: (input: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", input, { auth: false }),

  me: () => api.get<User>("/auth/me"),

  logout: () => api.post<void>("/auth/logout"),
};
