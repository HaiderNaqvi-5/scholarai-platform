import { api } from "../client";
import type { HealthResponse, PlatformAnalytics } from "../types";

export const analytics = {
  health: () => api.get<HealthResponse>("/health", { auth: false }),
  platform: () => api.get<PlatformAnalytics>("/analytics"),
};
