import { api } from "../client";
import type { DocumentDetail, DocumentSummary } from "../types";

export const mentors = {
  pending: (limit = 20) =>
    api.get<{ items: DocumentSummary[]; total: number }>("/mentors/pending-reviews", {
      query: { limit },
    }),

  document: (id: string) => api.get<DocumentDetail>(`/mentors/documents/${id}`),

  submitFeedback: (
    id: string,
    input: {
      summary: string;
      strengths: string[];
      revision_priorities: string[];
      caution_notes?: string[];
    },
  ) =>
    api.post<{ ok: true; reviewed_at: string }>(`/mentors/documents/${id}/feedback`, input),
};
