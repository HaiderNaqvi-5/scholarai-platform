import { api } from "../client";
import type { ProfessorEmailRequest, ProfessorEmailResponse } from "../types";

export const professorEmail = {
  /** POST /documents/professor-email — Elite-gated (402 for free/pro). */
  generate: (body: ProfessorEmailRequest) =>
    api.post<ProfessorEmailResponse>("/documents/professor-email", body),
};
