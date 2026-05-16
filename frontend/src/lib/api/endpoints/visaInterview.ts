import { api } from "../client";
import type {
  VisaInterviewAnswerRequest,
  VisaInterviewAnswerResponse,
  VisaInterviewSessionSummary,
  VisaInterviewStartRequest,
  VisaInterviewStartResponse,
} from "../types";

export const visaInterview = {
  start: (body: VisaInterviewStartRequest) =>
    api.post<VisaInterviewStartResponse>("/interviews/visa/start", body),
  /** Free tier is cut off after Q3 — answer() then throws a 402. */
  answer: (sessionId: string, body: VisaInterviewAnswerRequest) =>
    api.post<VisaInterviewAnswerResponse>(
      `/interviews/visa/${sessionId}/answer`,
      body,
    ),
  summary: (sessionId: string) =>
    api.get<VisaInterviewSessionSummary>(`/interviews/visa/${sessionId}/summary`),
};
