import { api } from "../client";
import type { ScholarshipMatchRequest, ScholarshipMatchResponse } from "../types";

export const scholarshipMatch = {
  /** POST /scholarships/match — body fields override the student profile. */
  match: (body: ScholarshipMatchRequest = {}) =>
    api.post<ScholarshipMatchResponse>("/scholarships/match", body),
};
