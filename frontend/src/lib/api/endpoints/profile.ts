import { api } from "../client";
import type { StudentProfile } from "../types";

export const profile = {
  get: () => api.get<StudentProfile>("/profile"),
  upsert: (input: Partial<StudentProfile>) => api.put<StudentProfile>("/profile", input),
};
