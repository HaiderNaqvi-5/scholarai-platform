import { api } from "../client";
import type { SavedOpportunity, SavedStatus } from "../types";

export const saved = {
  list: () => api.get<{ items: SavedOpportunity[] }>("/saved-opportunities"),
  add: (scholarshipId: string) =>
    api.post<SavedOpportunity>(`/saved-opportunities/${scholarshipId}`),
  setStatus: (scholarshipId: string, status: SavedStatus) =>
    api.patch<SavedOpportunity>(`/saved-opportunities/${scholarshipId}/status`, { status }),
  remove: (scholarshipId: string) =>
    api.delete<void>(`/saved-opportunities/${scholarshipId}`),
};
