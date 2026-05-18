import { api } from "../client";
import type { TokenResponse, User } from "../types";

export type SignupInput = {
  email: string;
  password: string;
  full_name: string;
  terms_version: string;
  privacy_version: string;
  accepted: boolean;
  marketing_consent?: boolean;
  billing_country?: string;
  invite_code?: string;
  air_uni_uni?: string;
  air_uni_dept?: string;
  air_uni_batch?: number;
};

export const auth = {
  register: (input: SignupInput) =>
    api.post<User>("/auth/register", input, { auth: false }),

  login: (input: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", input, { auth: false }),

  me: () => api.get<User>("/auth/me"),

  logout: () => api.post<void>("/auth/logout"),
};
