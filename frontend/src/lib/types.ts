export type StudentProfile = {
  citizenship_country_code: string;
  gpa_value: number | null;
  gpa_scale: number;
  target_field: string;
  target_degree_level: "MS";
  target_country_code: string;
  language_test_type: string | null;
  language_test_score: number | null;
};

export type ScholarshipListItem = {
  scholarship_id: string;
  title: string;
  provider_name: string | null;
  deadline_at: string | null;
  country_code: string;
  record_state: "published";
};

export type RecommendationItem = ScholarshipListItem & {
  estimated_fit_score: number;
  fit_band: "strong" | "possible" | "watch";
  top_reasons: string[];
  warnings: string[];
};

export type ApiError = {
  code: string;
  message: string;
  requestId?: string;
  status: number;
};
