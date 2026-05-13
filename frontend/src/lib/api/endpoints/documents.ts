import { api } from "../client";
import type { DocumentDetail, DocumentSummary } from "../types";

export const documents = {
  list: () => api.get<{ items: DocumentSummary[]; total: number }>("/documents"),
  detail: (id: string) => api.get<DocumentDetail>(`/documents/${id}`),

  submit: (input: {
    document_type: string;
    title: string;
    content_text?: string;
    file?: File;
    scholarship_ids?: string[];
  }) => {
    const fd = new FormData();
    fd.append("document_type", input.document_type);
    fd.append("title", input.title);
    if (input.content_text) fd.append("content_text", input.content_text);
    if (input.file) fd.append("file", input.file);
    for (const sid of input.scholarship_ids ?? []) fd.append("scholarship_ids", sid);
    return api.upload<DocumentDetail>("/documents", fd);
  },

  refreshFeedback: (id: string) =>
    api.post<DocumentDetail>(`/documents/${id}/feedback`),
};
