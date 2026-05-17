import { api } from "../client";
import type {
  LegalDocument,
  ConsentState,
  ConsentGrantInput,
  DataExportResponse,
  DataDeletionRequestResponse,
  DataDeletionCreateInput,
} from "../types";

/**
 * /privacy/legal/{slug} + /privacy/consent client.
 * Backend: backend/app/api/v1/routes/privacy.py
 */
export const legal = {
  document: (slug: string) =>
    api.get<LegalDocument>(`/privacy/legal/${encodeURIComponent(slug)}`, { auth: false }),

  consentState: () => api.get<ConsentState>("/privacy/consent"),

  grant: (input: ConsentGrantInput) =>
    api.post<ConsentState>("/privacy/consent", input),
};

export const privacy = {
  requestExport: () => api.post<DataExportResponse>("/privacy/data-export"),
  exportStatus: (id: string) =>
    api.get<DataExportResponse>(`/privacy/data-export/${encodeURIComponent(id)}`),
  scheduleDeletion: (input: DataDeletionCreateInput) =>
    api.post<DataDeletionRequestResponse>("/privacy/account-deletion", input),
  cancelDeletion: () => api.delete<void>("/privacy/account-deletion"),
};
