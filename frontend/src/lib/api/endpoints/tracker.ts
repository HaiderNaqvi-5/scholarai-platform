import { api } from "../client";
import type {
  TrackerChecklist,
  TrackerItem,
  TrackerItemCreateRequest,
  TrackerListResponse,
  TrackerStage,
} from "../types";

export const tracker = {
  list: () => api.get<TrackerListResponse>("/tracker"),
  create: (body: TrackerItemCreateRequest) =>
    api.post<TrackerItem>("/tracker", body),
  setStage: (id: string, stage: TrackerStage) =>
    api.patch<TrackerItem>(`/tracker/${id}/stage`, { stage }),
  /** Backend replaces the whole checklist — send all 14 keys, not a Partial. */
  setChecklist: (id: string, checklist: TrackerChecklist) =>
    api.patch<TrackerItem>(`/tracker/${id}/checklist`, { checklist }),
  remove: (id: string) => api.delete<void>(`/tracker/${id}`),
};
