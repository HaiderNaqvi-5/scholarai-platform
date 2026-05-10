import { api } from "../client";
import type { RecommendationListResponse } from "../types";

export const recommendations = {
  build: (limit = 10) =>
    api.post<RecommendationListResponse>("/recommendations", { limit }),

  evaluate: (input: {
    predicted_ids: string[];
    judged_relevance: Record<string, number>;
    k_values?: number[];
  }) =>
    api.post<{
      precision_at_k: Record<string, number>;
      recall_at_k: Record<string, number>;
      ndcg_at_k: Record<string, number>;
      mrr_at_k: Record<string, number>;
      kpi_gates: { name: string; passed: boolean }[];
      policy_version: string;
    }>("/recommendations/evaluate", input),

  benchmarks: () =>
    api.get<{
      items: {
        dataset_id: string;
        version: string;
        title: string;
        frozen_at: string;
        case_count: number;
        k_values: number[];
      }[];
    }>("/recommendations/benchmarks"),

  evaluateBenchmark: (datasetId: string) =>
    api.post<{
      dataset_id: string;
      case_results: { case_id: string; metrics: Record<string, number> }[];
      aggregate: Record<string, number>;
      pass_rate: number;
    }>(`/recommendations/benchmarks/${datasetId}/evaluate`),
};
