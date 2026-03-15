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
  match_summary: string;
  matched_criteria: string[];
  constraint_notes: string[];
  top_reasons: string[];
  warnings: string[];
};

export type RecommendationListResponse = {
  items: RecommendationItem[];
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

export type InterviewSessionStatus =
  | "not_started"
  | "in_progress"
  | "completed";

export type InterviewPracticeMode = "general";

export type InterviewRubricDimension = {
  dimension: "clarity" | "relevance" | "confidence" | "specificity";
  score: number;
  band: "early" | "developing" | "solid" | "strong";
  rationale: string;
};

export type InterviewAnswerFeedback = {
  question_index: number;
  question_text: string;
  answer_text: string;
  overall_score: number;
  overall_band: "early" | "developing" | "solid" | "strong";
  scoring_mode: string;
  summary_feedback: string;
  strengths: string[];
  improvement_prompts: string[];
  dimensions: InterviewRubricDimension[];
  limitation_notice: string;
  created_at: string | null;
};

export type InterviewCurrentQuestion = {
  session_id: string;
  status: InterviewSessionStatus;
  practice_mode: InterviewPracticeMode;
  question_index: number;
  total_questions: number;
  question_text: string | null;
};

export type InterviewSessionSummary = {
  session_id: string;
  status: InterviewSessionStatus;
  practice_mode: InterviewPracticeMode;
  current_question_index: number;
  total_questions: number;
  current_question: InterviewCurrentQuestion | null;
  responses: InterviewAnswerFeedback[];
  latest_feedback: InterviewAnswerFeedback | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CurationRecordState = "raw" | "validated" | "published" | "archived";

export type CurationRecordSummary = {
  record_id: string;
  title: string;
  provider_name: string | null;
  country_code: string;
  record_state: CurationRecordState;
  source_url: string;
  source_type: string | null;
  imported_at: string | null;
  source_last_seen_at: string | null;
  last_reviewed_at: string | null;
  validated_at: string | null;
  published_at: string | null;
  review_notes: string | null;
};

export type CurationRecordDetail = CurationRecordSummary & {
  summary: string | null;
  funding_summary: string | null;
  field_tags: string[];
  degree_levels: string[];
  citizenship_rules: string[];
  min_gpa_value: number | null;
  source_document_ref: string | null;
  provenance_payload: Record<string, unknown> | null;
  reviewed_by_user_id: string | null;
  validated_by_user_id: string | null;
  published_by_user_id: string | null;
  rejected_at: string | null;
  unpublished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CurationRecordListResponse = {
  items: CurationRecordSummary[];
};

export type ApiError = {
  code: string;
  message: string;
  request_id?: string;
  status: number;
};
