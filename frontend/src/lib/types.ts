export type StudentProfile = {
  id?: string;
  user_id?: string;
  citizenship_country_code: string;
  gpa_value: number | null;
  gpa_scale: number;
  target_field: string;
  target_degree_level: "MS";
  target_country_code: string;
  language_test_type: string | null;
  language_test_score: number | null;
};

export type UserSession = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type ScholarshipListItem = {
  scholarship_id: string;
  title: string;
  provider_name: string | null;
  deadline_at: string | null;
  country_code: string;
  record_state: "published";
};

export type SavedOpportunityItem = ScholarshipListItem & {
  saved_at: string;
};

export type SavedOpportunityListResponse = {
  items: SavedOpportunityItem[];
};

export type RecommendationItem = ScholarshipListItem & {
  estimated_fit_score: number;
  fit_band: "strong" | "possible" | "watch";
  top_reasons: string[];
  warnings: string[];
};

export type DocumentType = "sop" | "essay";
export type DocumentInputMethod = "text" | "file";
export type DocumentProcessingStatus =
  | "submitted"
  | "processing"
  | "completed"
  | "failed";

export type DocumentFeedback = {
  id: string;
  status: DocumentProcessingStatus;
  summary: string;
  strengths: string[];
  revision_priorities: string[];
  caution_notes: string[];
  citations: string[];
  grounded_context: string[];
  limitation_notice: string;
  completed_at: string | null;
};

export type DocumentRecordSummary = {
  id: string;
  title: string;
  document_type: DocumentType;
  input_method: DocumentInputMethod;
  processing_status: DocumentProcessingStatus;
  original_filename: string | null;
  created_at: string;
  updated_at: string;
  latest_feedback_at: string | null;
};

export type DocumentDetail = DocumentRecordSummary & {
  content_text: string;
  latest_feedback: DocumentFeedback | null;
};

export type DocumentListResponse = {
  items: DocumentRecordSummary[];
};

export type DocumentSubmissionResponse = {
  document: DocumentDetail;
};

export type ApiError = {
  code: string;
  message: string;
  request_id?: string;
  status: number;
};
