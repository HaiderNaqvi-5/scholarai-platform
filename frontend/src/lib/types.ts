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
  tracker_status: "saved" | "in_progress" | "applied" | "closed";
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
  retrieval_source?: string;
  semantic_similarity?: number | null;
  rule_pass_count?: number;
  rule_total_count?: number;
  heuristic_factors?: Record<string, number>;
  fallback_reason?: string | null;
  eligibility_graph?: Record<string, unknown>;
  signal_language?: {
    facts_label: string;
    estimated_signals_label: string;
    estimated_signals_notice: string;
  } | null;
  rationale?: {
    summary: string;
    facts: Array<{
      code: string;
      label: string;
      detail: string;
      stage: "scope" | "eligibility" | "retrieval" | "rerank" | "explanation";
      source:
        | "published_record"
        | "validated_rule"
        | "profile_input"
        | "retrieval_model"
        | "rerank_model";
      direction: "supports" | "limits" | "neutral";
      numeric_value?: number | null;
      display_value?: string | null;
    }>;
    estimated_signals: Array<{
      code: string;
      label: string;
      detail: string;
      stage: "scope" | "eligibility" | "retrieval" | "rerank" | "explanation";
      source:
        | "published_record"
        | "validated_rule"
        | "profile_input"
        | "retrieval_model"
        | "rerank_model";
      direction: "supports" | "limits" | "neutral";
      numeric_value?: number | null;
      display_value?: string | null;
    }>;
    stages: {
      scope: {
        status: "applied" | "fallback" | "skipped";
        summary: string;
      };
      eligibility: {
        status: "applied" | "fallback" | "skipped";
        summary: string;
      };
      retrieval: {
        status: "applied" | "fallback" | "skipped";
        summary: string;
      };
      rerank: {
        status: "applied" | "fallback" | "skipped";
        summary: string;
      };
      explanation: {
        status: "applied" | "fallback" | "skipped";
        summary: string;
      };
    };
  } | null;
};

export type RecommendationListResponse = {
  items: RecommendationItem[];
  total: number;
  meta?: {
    scope_policy: string;
    allowed_country_codes: string[];
    exception_policy: string;
    pipeline_version: string;
  };
};

export type DocumentType = "sop" | "essay";
export type DocumentInputMethod = "text" | "file";
export type DocumentProcessingStatus =
  | "submitted"
  | "processing"
  | "completed"
  | "failed";

export type DocumentGroundingEntry =
  | string
  | {
      label?: string | null;
      detail?: string | null;
      value?: string | null;
      source?: string | null;
      citation?: string | null;
      scholarship_id?: string | null;
    };

export type DocumentGeneratedGuidance = {
  summary: string;
  strengths: string[];
  revision_priorities: string[];
  caution_notes: string[];
};

export type DocumentCitation = {
  source_id: string;
  title: string;
  url_or_ref: string;
  snippet: string;
  relevance_score: number;
};

export type DocumentFeedback = {
  id: string;
  status: DocumentProcessingStatus;
  summary: string;
  strengths: string[];
  revision_priorities: string[];
  caution_notes: string[];
  citations: DocumentCitation[];
  grounding_score: number;
  coverage_flags: Record<string, boolean>;
  ungrounded_warnings: string[];
  grounded_context: DocumentGroundingEntry[];
  limitation_notice: string;
  validated_facts?: DocumentGroundingEntry[] | null;
  retrieved_writing_guidance?: DocumentGroundingEntry[] | null;
  generated_guidance?: DocumentGeneratedGuidance | null;
  limitations?: string[] | null;
  grounded_context_sections?: {
    validated_facts: DocumentGroundingEntry[];
    retrieved_writing_guidance: DocumentGroundingEntry[];
    generated_guidance: Array<{ type: string; guidance: string }>;
    limitations: string[];
  } | null;
  completed_at: string | null;
};

export type DocumentRecordSummary = {
  id: string;
  title: string;
  document_type: DocumentType;
  scholarship_id?: string | null;
  scholarship_ids?: string[] | null;
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

export type InterviewPracticeMode = "general" | "scholarship";

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
  scholarship_id?: string | null;
  status: InterviewSessionStatus;
  practice_mode: InterviewPracticeMode;
  current_question_index: number;
  total_questions: number;
  current_question: InterviewCurrentQuestion | null;
  responses: InterviewAnswerFeedback[];
  latest_feedback: InterviewAnswerFeedback | null;
  history_summary: {
    answered_count: number;
    recent_answers: Array<{
      question_index: number;
      question_text: string;
      overall_score: number;
      weakest_dimension: string | null;
      strongest_dimension: string | null;
      improvement_focus: string | null;
    }>;
  };
  trend_summary: {
    average_score: number | null;
    score_delta: number | null;
    score_direction: string;
    weakest_dimension_overall: string | null;
    latest_weakest_dimension: string | null;
    dimension_averages: Record<string, number>;
  };
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

export type IngestionExecutionMode = "inline" | "worker" | "auto";

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
  execution_mode_requested: IngestionExecutionMode | null;
  execution_mode_selected: IngestionExecutionMode | null;
  dispatch_status: string | null;
  celery_task_id: string | null;
  attempt_count: number | null;
  run_retry_count: number | null;
  last_started_at: string | null;
  last_retry_requested_at: string | null;
  failure_phase: string | null;
  review_queue: string | null;
  queue_assigned_by_user_id: string | null;
  queue_assigned_at: string | null;
  queue_assignment_note: string | null;
  snapshot_available: boolean;
  snapshot_captured_at: string | null;
  snapshot_content_length: number | null;
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
  execution_mode?: IngestionExecutionMode;
};

export type IngestionRunRetryRequest = {
  max_records?: number | null;
  execution_mode?: IngestionExecutionMode | null;
};

export type IngestionRunQueueAssignmentRequest = {
  queue_key: string;
  note?: string | null;
};

export type IngestionRunBulkRetryRequest = {
  run_ids: string[];
  max_records?: number | null;
  execution_mode?: IngestionExecutionMode | null;
};

export type IngestionRunBulkRetryItem = {
  run_id: string;
  status: "retried" | "skipped" | "failed";
  message: string;
  detail: IngestionRunDetail | null;
};

export type IngestionRunBulkRetryResponse = {
  items: IngestionRunBulkRetryItem[];
  total: number;
  retried: number;
  skipped: number;
  failed: number;
};

export type IngestionRunSnapshotResponse = {
  run_id: string;
  available: boolean;
  html_content: string | null;
  captured_at: string | null;
  content_length: number | null;
  truncated: boolean;
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

export type AccessControlManagedUser = {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  auth_token_version: number;
  effective_capabilities: string[];
};

export type AccessControlManagedUserListResponse = {
  items: AccessControlManagedUser[];
  total: number;
};

export type AccessControlRoleChangeItem = {
  audit_id: string;
  target_user_id: string;
  actor_user_id: string | null;
  action: "access_control.role.update" | "access_control.role.revert";
  previous_role: string;
  next_role: string;
  reason: string | null;
  changed_at: string;
  reverted_by_audit_id: string | null;
  is_reversible: boolean;
};

export type AccessControlRoleChangeListResponse = {
  items: AccessControlRoleChangeItem[];
  total: number;
};
