import { api } from "../client";
import type { CurationRecord, CurationState, IngestionRun } from "../types";

export const curation = {
  startRun: (input: { source_key: string; execution_mode?: "inline" | "worker" }) =>
    api.post<IngestionRun>("/curation/ingestion-runs", input),

  listRuns: (filters: {
    page?: number;
    page_size?: number;
    status?: string;
    source_key?: string;
    dispatch_status?: string;
  } = {}) =>
    api.get<{ items: IngestionRun[]; total: number }>("/curation/ingestion-runs", { query: filters }),

  runDetail: (id: string) =>
    api.get<IngestionRun>(`/curation/ingestion-runs/${id}`),

  snapshot: (id: string) =>
    api.get<{ html_content: string; captured_at: string; content_length: number }>(
      `/curation/ingestion-runs/${id}/snapshot`,
    ),

  clearSnapshot: (id: string) =>
    api.delete<{ cleared: true }>(`/curation/ingestion-runs/${id}/snapshot`),

  retryRun: (id: string, input: { execution_mode?: "inline" | "worker"; max_records?: number } = {}) =>
    api.post<IngestionRun>(`/curation/ingestion-runs/${id}/retry`, input),

  bulkRetry: (run_ids: string[]) =>
    api.post<{ success_count: number; failed_ids: string[]; errors: Record<string, string> }>(
      "/curation/ingestion-runs/bulk-retry",
      { run_ids },
    ),

  assignQueue: (id: string, input: { review_queue: string; note?: string }) =>
    api.post<IngestionRun>(`/curation/ingestion-runs/${id}/assign-queue`, input),

  manualImport: (input: { source_key: string; payload: Record<string, unknown> }) =>
    api.post<CurationRecord>("/curation/imports", input),

  listRecords: (filters: { state?: CurationState; page?: number; page_size?: number } = {}) =>
    api.get<{ items: CurationRecord[]; total: number }>("/curation/records", { query: filters }),

  recordDetail: (id: string) => api.get<CurationRecord>(`/curation/records/${id}`),

  updateRecord: (id: string, input: { title?: string; fields?: Record<string, unknown> }) =>
    api.patch<CurationRecord>(`/curation/records/${id}`, input),

  approve: (id: string, note?: string) =>
    api.post<CurationRecord>(`/curation/records/${id}/approve`, { note }),
  reject: (id: string, note: string) =>
    api.post<CurationRecord>(`/curation/records/${id}/reject`, { note }),
  publish: (id: string, note?: string) =>
    api.post<CurationRecord>(`/curation/records/${id}/publish`, { note }),
  unpublish: (id: string, note?: string) =>
    api.post<CurationRecord>(`/curation/records/${id}/unpublish`, { note }),
};
