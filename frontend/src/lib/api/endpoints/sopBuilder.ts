import { api } from "../client";
import type { SOPDraftRequest, SOPDraftResponse } from "../types";

export const sopBuilder = {
  /** POST /documents/sop/draft — free tier is capped at 1 SOP (402 after). */
  draft: (body: SOPDraftRequest) =>
    api.post<SOPDraftResponse>("/documents/sop/draft", body),
};
