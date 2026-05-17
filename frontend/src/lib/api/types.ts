/**
 * Shared API types. Keep aligned with backend schemas in
 * scholarai-platform/backend/app/schemas/. Source of truth: backend.
 */

export type Role =
  | "enduser_student"
  | "student"
  | "mentor"
  | "admin"
  | "owner"
  | "dev"
  | "internal_user"
  | "university";

export type Plan = "free" | "pro" | "elite" | "institution";
export type Currency = "PKR" | "GBP" | "EUR" | "AED" | "USD";

export type User = {
  id: string;
  email: string;
  full_name?: string | null;
  role: Role;
  institution?: string | null;
  created_at?: string;
  /** Plan tier — backend exposes on /auth/me. Drives frontend gating. */
  plan: Plan;
  plan_currency: Currency;
  billing_country?: string | null;
  /** Trial expiry timestamp (null for non-trial plans). */
  plan_expires_at?: string | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

/**
 * StudentProfile — mirrors backend `StudentProfileResponse`
 * (backend/app/schemas/students.py). Backend allowed values are enforced
 * server-side; the literal unions here are documentation only — backend
 * is the source of truth.
 */
export type TargetDegreeLevel = "MS" | "PHD" | "MBA" | "MENG" | "BS";
export type HecDegreeLevel = "bachelor" | "master" | "mphil";
export type CgpaScaleChoice = "4.0" | "4.0_hec";
export type FundingRequirement = "fully_funded_only" | "partial_ok" | "self_funded_ok";
export type IntakeTarget = "jan_2025" | "sep_2025" | "jan_2026" | "sep_2026" | "flexible";

export type StudentProfile = {
  id: string;
  user_id: string;

  // Core eligibility
  citizenship_country_code: string;
  gpa_value: number | null;
  gpa_scale: number;
  target_field: string;
  target_degree_level: TargetDegreeLevel;

  // Legacy single-country (kept for back-compat — derived from target_countries[0])
  target_country_code: string;

  // Pakistan-pivot multi-select
  target_countries: string[];
  target_fields: string[];

  // Language test
  language_test_type: string | null;
  language_test_score: number | null;

  // Pakistani academic context
  hec_degree_level: HecDegreeLevel | null;
  pakistani_university: string | null;
  cgpa_scale_choice: CgpaScaleChoice | null;
  degree_subject: string | null;
  graduation_year: number | null;

  // Test scores
  ielts_score: number | null;
  toefl_score: number | null;
  gre_quant: number | null;
  gre_verbal: number | null;

  // Research
  has_research_publications: boolean | null;
  research_publication_count: number | null;

  // Goals
  funding_requirement: FundingRequirement | null;
  intake_target: IntakeTarget | null;
  city_of_origin: string | null;

  // Financial context
  can_afford_application_fees: boolean | null;
  needs_gre_waiver: boolean | null;
  family_has_funds_for_bank_statement: boolean | null;
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

// ───────────────────────────────────────────────────────────────────────────
// Pakistan pivot — Frontend Pass. Hand-synced to backend Pydantic schemas:
//   tracker.py · scholarships_match.py · sop.py · professor_email.py
//   visa_interview.py · waitlist.py · reports.py
// ───────────────────────────────────────────────────────────────────────────

/** HTTP 402 detail from core/plan_guard.py. `required_plan` is a list. */
export type PlanRequiredDetail = {
  error: string;
  required_plan: string[];
  current_plan: string;
  upgrade_url: string;
  price: string;
  message: string;
  partial_summary?: Record<string, unknown> | null;
};

// ── Application tracker (PRD §6) ───────────────────────────────────────────

// Tracker stage + checklist live next to their display metadata in
// `lib/tracker/`; re-export here so API consumers see one shape.
export type { TrackerStage } from "@/lib/tracker/stages";
export { TRACKER_STAGES, STAGE_META, stageLabel } from "@/lib/tracker/stages";
export type {
  TrackerChecklist,
  TrackerChecklistKey,
} from "@/lib/tracker/checklist";
export {
  CHECKLIST_LABELS,
  CHECKLIST_KEYS,
  checklistProgress,
} from "@/lib/tracker/checklist";

import type { TrackerStage } from "@/lib/tracker/stages";
import type { TrackerChecklist } from "@/lib/tracker/checklist";

export type TrackerItem = {
  id: string;
  user_id: string;
  scholarship_id?: string | null;
  university_id?: string | null;
  program_name?: string | null;
  university_name?: string | null;
  country?: string | null;
  stage: TrackerStage;
  deadline?: string | null;
  notes?: string | null;
  document_checklist: TrackerChecklist;
  created_at: string;
  updated_at: string;
};

export type TrackerListResponse = {
  items: TrackerItem[];
  total: number;
  plan_limit?: number | null;
  plan: Plan;
};

export type TrackerItemCreateRequest = {
  scholarship_id?: string | null;
  university_id?: string | null;
  program_name?: string | null;
  university_name?: string | null;
  country?: string | null;
  stage?: TrackerStage;
  deadline?: string | null;
  notes?: string | null;
};

// ── Scholarship match (PRD §5) ─────────────────────────────────────────────
// Public shape mirrors backend `scholarships_match.py` (Task 7 retier).
// Neutral fields only — no internal bucket vocabulary leaks here.

export type ScholarshipMatchRequest = {
  cgpa?: number | null;
  degree_target?: string | null;
  fields?: string[];
  countries?: string[];
  has_ielts?: boolean | null;
  ielts_score?: number | null;
  has_gre?: boolean | null;
  funding_requirement?: string | null;
  nationality?: string | null;
};

export interface ScholarshipMatchOut {
  id: string | null; // UUID
  name: string;
  provider: string;
  country_code: string | null;
  funding_amount: string | null;
  deadline: string | null; // ISO date
  compatibility: number; // 0..1
  locked: boolean;
}

export interface UnlockOffer {
  to_plan: "pro" | "elite";
  locked_count: number;
  headline: string;
  message: string;
}

export interface MatchResponse {
  items: ScholarshipMatchOut[];
  unlock_offer: UnlockOffer | null;
}

// Backwards-compatible alias used by existing callers.
export type ScholarshipMatchResponse = MatchResponse;

// ── SOP builder (PRD §7) ───────────────────────────────────────────────────

export type SOPInputs = {
  academic_background: string;
  research_experience?: string | null;
  professional_experience?: string | null;
  why_this_program: string;
  why_this_country?: string | null;
  career_goals: string;
  challenges_overcome?: string | null;
  gap_explanation?: string | null;
};

export type SOPDraftRequest = {
  scholarship_id?: string | null;
  university_id?: string | null;
  program_name?: string | null;
  sop_inputs: SOPInputs;
};

export type SOPParagraphFeedback = {
  index: number;
  paragraph_label: string;
  strength: string;
  weakness: string;
  suggestion: string;
};

export type SOPGroundedContext = {
  validated_scholarship_facts: string[];
  retrieved_writing_guidance: string[];
  generated_guidance?: string | null;
  limitations: string;
};

export type SOPDraftResponse = {
  document_id: string;
  document_type: string;
  draft_content: string;
  word_count: number;
  paragraph_labels: string[];
  grounded_context: SOPGroundedContext;
  line_feedback?: SOPParagraphFeedback[] | null;
  model_used: string;
  used_llm: boolean;
  created_at: string;
};

// ── Professor cold-email generator (PRD §0.6, Elite) ───────────────────────

export type ProfessorEmailRequest = {
  professor_name: string;
  university: string;
  research_area: string;
  student_pitch: string;
  position_type?: "phd" | "ra";
};

export type ProfessorEmailResponse = {
  document_id: string;
  document_type: string;
  email_subject: string;
  email_body: string;
  word_count: number;
  used_llm: boolean;
  model_used: string;
  limitations: string;
  created_at: string;
};

// ── Visa interview simulator (PRD §8) ──────────────────────────────────────

export type VisaCountry = "GB" | "US" | "CA" | "DE";
export type VisaPracticeMode = "study" | "exam";

export type VisaInterviewStartRequest = {
  country: VisaCountry;
  visa_type?: string | null;
  practice_mode?: VisaPracticeMode;
  scholarship_id?: string | null;
};

export type VisaInterviewQuestion = {
  id: string;
  country: string;
  visa_type: string;
  category: string;
  question_text: string;
  difficulty: string;
};

export type VisaInterviewStartResponse = {
  session_id: string;
  country: string;
  visa_type: string;
  practice_mode: string;
  total_questions: number;
  first_question?: VisaInterviewQuestion | null;
  started_at: string;
};

export type VisaInterviewAnswerRequest = {
  question_id: string;
  answer_text: string;
};

export type VisaInterviewRubric = {
  clarity_score: number;
  confidence_score: number;
  relevance_score: number;
  overall_score: number;
  red_flags: string[];
  missing_elements: string[];
  what_was_good: string;
  ideal_answer_summary: string;
  used_llm: boolean;
};

export type VisaInterviewProgress = {
  answered: number;
  total: number;
};

export type VisaInterviewAnswerResponse = {
  evaluation: VisaInterviewRubric;
  next_question?: VisaInterviewQuestion | null;
  session_progress: VisaInterviewProgress;
  partial_summary?: Record<string, unknown> | null;
};

export type VisaInterviewSessionSummary = {
  session_id: string;
  country: string;
  visa_type: string;
  answered: number;
  total: number;
  average_score: number;
  score_breakdown: Record<string, number>;
  red_flag_count: number;
  areas_to_improve: string[];
  transcript_document_id?: string | null;
};

// ── Upgrade / pricing / waitlist (PRD §0.5) ────────────────────────────────

export type PricingTier = {
  key: string;
  label: string;
  is_recommended: boolean;
  monthly_price: string;
  yearly_hint?: string | null;
  feature_summary: string;
  bullet_features: string[];
};

export type PricingResponse = {
  currency: Currency;
  tiers: PricingTier[];
};

export type WaitlistJoinRequest = {
  email: string;
  plan?: "pro" | "elite" | "institution";
  currency?: Currency;
  country?: string | null;
};

export type WaitlistJoinResponse = {
  id: string;
  email: string;
  plan: string;
  currency: string;
  created_at: string;
};

// ── Application strategy report (PRD §0.6, Elite) ──────────────────────────

export type StrategyReportRequest = {
  notes?: string | null;
};

export type ReportProfileSummary = {
  full_name?: string | null;
  pakistani_university?: string | null;
  cgpa_value?: number | null;
  cgpa_us_equivalent?: number | null;
  uk_degree_class?: string | null;
  ielts_score?: number | null;
  target_degree?: string | null;
  target_countries: string[];
  target_fields: string[];
  funding_requirement?: string | null;
};

export type ReportUniversityMatch = {
  university_id: string;
  name: string;
  country: string;
  tier: "Safety" | "Target" | "Reach";
  reason: string;
};

export type ReportScholarshipMatch = {
  scholarship_id: string;
  title: string;
  country_code: string;
  funding_type?: string | null;
  deadline_days?: number | null;
  match_reason: string;
};

export type ReportActionPlan = {
  next_30_days: string[];
  next_60_days: string[];
  next_90_days: string[];
};

export type StrategyReportResponse = {
  document_id: string;
  document_type: string;
  profile_summary: ReportProfileSummary;
  universities: ReportUniversityMatch[];
  scholarships: ReportScholarshipMatch[];
  action_plan: ReportActionPlan;
  generated_guidance: string;
  limitations: string;
  used_llm: boolean;
  created_at: string;
};

// ── Legal documents + consent (Front-upgrade §6.4, backend privacy.py) ─────

export type LegalDocument = {
  slug: string;
  version: string;
  effective_at: string;
  body_markdown: string;
  sha256_hash: string;
};

export type ConsentType =
  | "terms"
  | "privacy"
  | "marketing"
  | "b2b_share"
  | "cookies"
  | "aup";

export type ConsentRecord = {
  consent_type: ConsentType;
  version: string;
  granted: boolean;
  granted_at: string | null;
};

export type ConsentState = {
  records: ConsentRecord[];
  current_versions: Partial<Record<ConsentType, string>>;
};

export type ConsentGrantInput = {
  consent_type: ConsentType;
  version: string;
  granted: boolean;
};

export type DataExportResponse = {
  id: string;
  status: string;
  requested_at: string;
  completed_at: string | null;
  download_url: string | null;
  expires_at: string | null;
};

export type DataDeletionRequestResponse = {
  id: string;
  status: string;
  requested_at: string;
  scheduled_for: string;
  cancelled_at: string | null;
  executed_at: string | null;
};

export type DataDeletionCreateInput = {
  reason?: string | null;
};

