/**
 * Shared API types. Keep aligned with backend schemas in
 * scholarai-platform/backend/app/schemas/. Source of truth: backend.
 */

export type Role =
  | "ENDUSER_STUDENT"
  | "MENTOR"
  | "ADMIN"
  | "OWNER"
  | "DEV"
  | "INTERNAL_USER"
  | "UNIVERSITY";

export type User = {
  id: string;
  email: string;
  full_name?: string | null;
  role: Role;
  institution?: string | null;
  created_at?: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type StudentProfile = {
  user_id: string;
  full_name: string;
  citizenship: string;
  language_scores?: { test: string; score: number }[] | null;
  gpa?: number | null;
  gpa_scale?: number | null;
  degree_level?: "BS" | "MS" | "PHD" | null;
  field_tags?: string[] | null;
  graduation_year?: number | null;
  updated_at?: string;
};

export type Scholarship = {
  id: string;
  title: string;
  provider: string;
  country_code: string;
  field_tags: string[];
  degree_level: "BS" | "MS" | "PHD" | string;
  funding_type: "TUITION" | "TUITION_STIPEND" | "TRAVEL" | "FULL" | string;
  amount_min?: number | null;
  amount_max?: number | null;
  currency?: string | null;
  deadline?: string | null;
  source_url?: string | null;
  min_gpa?: number | null;
  citizenship_rules?: string[];
  language_requirements?: { test: string; min_score: number }[];
  requirements?: string[];
  description?: string | null;
  published_at?: string | null;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type ScholarshipListResponse = Paginated<Scholarship> & {
  applied_filters?: Record<string, unknown>;
};

export type RecommendationStage = {
  name: "scope" | "eligibility" | "retrieval" | "rerank" | string;
  status: "passed" | "applied" | "skipped" | "failed" | string;
  detail?: string;
};

export type RecommendationItem = {
  scholarship: Scholarship;
  rank: number;
  stages: RecommendationStage[];
  supporting_factors: string[];
  limiting_factors: string[];
  /** Calibrated heuristic score; never shown to user as probability. */
  score?: number;
};

export type RecommendationListResponse = {
  items: RecommendationItem[];
  scope_policy: string;
  pipeline_version: string;
  generated_at: string;
};

export type SavedStatus = "saved" | "in_progress" | "applied" | "closed";

export type SavedOpportunity = {
  scholarship_id: string;
  scholarship: Scholarship;
  status: SavedStatus;
  saved_at: string;
  status_changed_at?: string;
  notes?: string | null;
};

export type DocumentType = "SOP" | "ESSAY" | "RESEARCH_STATEMENT" | "MOTIVATION_LETTER" | string;
export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export type DocumentFeedbackPartition = {
  validated_facts: { text: string; source_url?: string }[];
  retrieved_writing_guidance: { text: string; source?: string }[];
  generated_guidance: { text: string }[];
  limitations: string[];
};

export type DocumentSummary = {
  id: string;
  title: string;
  document_type: DocumentType;
  processing_status: DocumentStatus;
  created_at: string;
  updated_at?: string;
  scholarship_ids?: string[];
};

export type DocumentDetail = DocumentSummary & {
  content_text?: string | null;
  latest_feedback?: DocumentFeedbackPartition | null;
};

export type InterviewMode = "GENERAL" | "SCHOLARSHIP" | "TECHNICAL" | string;

export type InterviewRubricDimension = {
  dimension: string;
  score: number;
  trend?: "up" | "down" | "flat";
};

export type InterviewSession = {
  session_id: string;
  practice_mode: InterviewMode;
  scholarship_id?: string | null;
  status: "active" | "ended";
  questions_asked: number;
  rubric_scores: InterviewRubricDimension[];
  started_at: string;
  ended_at?: string | null;
};

export type InterviewQuestion = {
  question_text: string;
  dimension_focus: string;
  guidance_hint?: string;
  question_index: number;
};

export type IngestionRunStatus = "queued" | "running" | "succeeded" | "failed";

export type IngestionRun = {
  run_id: string;
  source_key: string;
  status: IngestionRunStatus;
  records_found?: number;
  execution_mode_selected?: "inline" | "worker";
  dispatch_status?: string;
  failure_phase?: string | null;
  capture_path?: string | null;
  started_at: string;
  finished_at?: string | null;
};

export type CurationState = "raw" | "validated" | "published";

export type CurationRecord = {
  record_id: string;
  state: CurationState;
  title: string;
  fields: Record<string, unknown>;
  audit_log: { actor: string; action: string; at: string; note?: string }[];
  rejection_reason?: string | null;
  published_at?: string | null;
};

export type RoleChangeAudit = {
  audit_id: string;
  target_user_id: string;
  actor_user_id: string;
  from_role: Role;
  to_role: Role;
  reason: string;
  changed_at: string;
  reverted_audit_id?: string | null;
};

export type HealthResponse = {
  status: "healthy" | "degraded";
  version: string;
  database: "ok" | "error";
  kpi_alerts: { domain: string; severity: "info" | "warn" | "critical"; message: string }[];
};

export type PlatformAnalytics = {
  total_users: number;
  student_count: number;
  mentor_count: number;
  admin_count: number;
  total_scholarships: number;
  applications_count: number;
  documents_count: number;
  interview_sessions_count: number;
  ingestion_runs_recent: { status: IngestionRunStatus; count: number }[];
  kpi_trends: Record<string, { points: { at: string; value: number }[] }>;
};
