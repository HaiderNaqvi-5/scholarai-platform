import { api } from "../client";
import type { InterviewQuestion, InterviewSession } from "../types";

export const interviews = {
  start: (input: { practice_mode: string; scholarship_id?: string }) =>
    api.post<InterviewSession>("/interviews", input),
  detail: (id: string) => api.get<InterviewSession>(`/interviews/${id}`),
  question: (id: string) =>
    api.get<InterviewQuestion>(`/interviews/${id}/question`),
  answer: (id: string, text_response: string) =>
    api.post<InterviewSession>(`/interviews/${id}/responses`, { text_response }),
  analytics: () =>
    api.get<{
      sessions: InterviewSession[];
      trends: Record<string, { points: { at: string; score: number }[] }>;
      recommended_focus: string[];
    }>("/interviews/coaching-analytics"),
};
