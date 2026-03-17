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

export type ScholarshipAppliedFilters = {
  country_code: string | null;
  query: string | null;
  field_tag: string | null;
  degree_level: string | null;
  provider: string | null;
  funding_type: string | null;
  min_amount: number | null;
  max_amount: number | null;
  has_deadline: boolean | null;
  deadline_within_days: number | null;
  deadline_after: string | null;
  deadline_before: string | null;
  sort: "deadline" | "title" | "recent";
};

export type ScholarshipListResponse = {
  items: ScholarshipListItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  applied_filters: ScholarshipAppliedFilters;
};

export type ScholarshipDetail = ScholarshipListItem & {
  summary: string | null;
  funding_summary: string | null;
  funding_type: string | null;
  funding_amount_min: number | null;
  funding_amount_max: number | null;
  source_url: string;
  field_tags: string[];
  degree_levels: string[];
  citizenship_rules: string[];
  min_gpa_value: number | null;
  source_document_ref: string | null;
  requirement_summary: string[];
  last_validated_at: string | null;
  published_at: string | null;
  publication_hint: string;
};

export type SavedOpportunityItem = ScholarshipListItem & {
  saved_at: string;
};

export type SavedOpportunityListResponse = {
  items: SavedOpportunityItem[];
  total: number;
};

export type RecommendationItem = ScholarshipListItem & {
  estimated_fit_score: number;
  fit_band: "strong" | "possible" | "watch";
  match_summary: string;
  matched_criteria: string[];
  constraint_notes: string[];
  top_reasons: string[];
  warnings: string[];
  shap_explanation?: Record<string, number> | null;
};

export type RecommendationListResponse = {
  items: RecommendationItem[];
  total: number;
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
  total: number;
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
  total: number;
  applied_state: CurationRecordState | null;
};

export type IngestionRunStatus =
  | "queued"
  | "running"
  | "completed"
  | "partial"
  | "failed";

export type IngestionRunSummary = {
  run_id: string;
  source_key: string;
  source_display_name: string;
  fetch_url: string;
  status: IngestionRunStatus;
  capture_mode: string | null;
  parser_name: string | null;
  records_found: number;
  records_created: number;
  records_skipped: number;
  failure_reason: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type IngestionRunDetail = IngestionRunSummary & {
  run_metadata: Record<string, unknown> | null;
};

export type IngestionRunListResponse = {
  items: IngestionRunSummary[];
  total: number;
};

export type IngestionRunStartRequest = {
  source_key: string;
  source_display_name?: string | null;
  source_base_url?: string | null;
  source_type: string;
  max_records: number;
};

export type CurationRawImportRequest = {
  source_key: string;
  source_display_name: string;
  source_base_url: string;
  source_type: string;
  title: string;
  provider_name: string | null;
  country_code: string;
  source_url: string;
  external_source_id: string | null;
  source_document_ref: string | null;
  summary: string | null;
  funding_summary: string | null;
  field_tags: string[];
  degree_levels: string[];
  citizenship_rules: string[];
  min_gpa_value: number | null;
  deadline_at: string | null;
  imported_at: string | null;
  source_last_seen_at: string | null;
  review_notes: string | null;
  provenance_payload: Record<string, unknown> | null;
};

export type ApiError = {
  code: string;
  message: string;
  request_id?: string;
  status: number;
};

export type MentorFeedbackRequest = {
  summary: string;
  strengths: string[];
  revision_priorities: string[];
  caution_notes: string[];
};

export type MentorFeedbackResponse = {
  id: string;
  document_id: string;
  mentor_id: string;
  summary: string;
  strengths: string[];
  revision_priorities: string[];
  caution_notes: string[];
  submitted_at: string | null;
};

export type PlatformAnalyticsResponse = {
  total_users: number;
  student_count: number;
  mentor_count: number;
  admin_count: number;
  total_scholarships: number;
  total_applications: number;
  submitted_applications: number;
  total_documents: number;
  total_interview_sessions: number;
  ingestion_runs_total: number;
  ingestion_runs_failed: number;
};
