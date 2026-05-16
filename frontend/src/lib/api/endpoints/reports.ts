import { api } from "../client";
import type { StrategyReportRequest, StrategyReportResponse } from "../types";

export const reports = {
  /** POST /reports/strategy — Elite-gated (402 for free/pro). */
  strategy: (body: StrategyReportRequest = {}) =>
    api.post<StrategyReportResponse>("/reports/strategy", body),
};
