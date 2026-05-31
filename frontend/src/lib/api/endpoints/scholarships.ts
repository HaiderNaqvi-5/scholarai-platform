import { api } from "../client";
import type {
  Scholarship,
  ScholarshipListItemResponse,
} from "../types";

export type ScholarshipFilters = {
  query?: string;
  country_code?: string;
  field_tag?: string;
  degree_level?: string;
  provider?: string;
  funding_type?: string;
  min_amount?: number;
  max_amount?: number;
  deadline_within_days?: number;
  sort?: "deadline" | "title" | "recent";
  page?: number;
  page_size?: number;
};

export const scholarships = {
  list: (filters: ScholarshipFilters = {}) =>
    api.get<ScholarshipListItemResponse>("/scholarships", { query: filters }),
  /** Alias of list — accurately-typed lean catalog read. Used by the marketing rail. */
  listPublic: (filters: ScholarshipFilters = {}) =>
    api.get<ScholarshipListItemResponse>("/scholarships", { query: filters }),
  detail: (id: string) => api.get<Scholarship>(`/scholarships/${id}`),
};
