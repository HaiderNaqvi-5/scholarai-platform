/**
 * routes.mjs — single manifest driving the audit runner.
 *
 * Each entry:
 *   { path, name, auth, states[], banned_extra[], expected_phrases[], waitFor? }
 *
 * auth:
 *   "public"  — no token
 *   "student" — log in as DEMO_STUDENT_EMAIL (default zara.khan@example.com)
 *   "admin"   — log in as DEMO_ADMIN_EMAIL
 *
 * states:
 *   "loaded"      — golden path (no mock)
 *   "empty"       — list endpoints return []
 *   "loading"     — endpoints stall 5s, capture mid-paint
 *   "processing"  — long-running mutation in flight (POST returns 202 + status=processing)
 *   "error"       — primary endpoint returns 500
 *   "locked402"   — primary endpoint returns 402 plan-required
 *
 * banned_extra[] adds to the global §7.5 ledger.
 * expected_phrases[] silences false positives (e.g. "smart card" in a citation).
 */

export const SYSTEM_ROUTES = [
  { path: "/not-found-test-trigger-404", name: "not-found", auth: "public", states: ["loaded"] },
  { path: "/offline", name: "offline", auth: "public", states: ["loaded"] },
  { path: "/denied", name: "denied", auth: "public", states: ["loaded"] },
  { path: "/maintenance", name: "maintenance", auth: "public", states: ["loaded"] },
];

export const PUBLIC_ROUTES = [
  { path: "/", name: "landing", auth: "public", states: ["loaded"] },
  { path: "/booth/air-university", name: "booth", auth: "public", states: ["loaded"] },
  { path: "/upgrade", name: "pricing", auth: "public", states: ["loaded"] },
  { path: "/signup", name: "signup", auth: "public", states: ["loaded"] },
  { path: "/signup?invite=AIRU2026", name: "signup-airu", auth: "public", states: ["loaded"] },
  { path: "/login", name: "login", auth: "public", states: ["loaded"] },
  { path: "/universities", name: "universities", auth: "public", states: ["loaded"] },
];

export const LEGAL_ROUTES = [
  { path: "/legal/terms", name: "legal-terms", auth: "public", states: ["loaded", "error"] },
  { path: "/legal/privacy", name: "legal-privacy", auth: "public", states: ["loaded", "error"] },
  { path: "/legal/dpa", name: "legal-dpa", auth: "public", states: ["loaded", "error"] },
  { path: "/legal/cookie", name: "legal-cookie", auth: "public", states: ["loaded", "error"] },
  { path: "/legal/refund", name: "legal-refund", auth: "public", states: ["loaded", "error"] },
];

/**
 * Stub bodies for dynamic-detail routes. Shapes mirror lib/api/types.ts so
 * the components render without 404 or TypeError. zara seed has 0 docs /
 * 0 interviews so we can't drive these with real IDs; mockOk via runner.mjs
 * injects these as the API response.
 */
// Shape mirrors lib/api/types.ts::DocumentDetail (= DocumentSummary + optional fields).
const DOCUMENT_DETAIL_STUB = {
  id: "stub-doc-1",
  title: "Stub SOP for audit",
  document_type: "SOP",
  processing_status: "completed",
  content_text: "This is a stubbed SOP body for the audit runner.",
  latest_feedback: {
    validated_facts: [],
    retrieved_writing_guidance: [],
    generated_guidance: [],
    limitations: [],
  },
  scholarship_ids: [],
  created_at: "2026-05-24T00:00:00Z",
  updated_at: "2026-05-24T00:00:00Z",
};

// Shape mirrors lib/api/types.ts::InterviewSession.
const INTERVIEW_DETAIL_STUB = {
  session_id: "stub-int-1",
  practice_mode: "GENERAL",
  scholarship_id: null,
  status: "ended",
  questions_asked: 3,
  rubric_scores: [
    { dimension: "clarity", score: 3.5, trend: "flat" },
    { dimension: "structure", score: 4.0, trend: "up" },
    { dimension: "evidence", score: 3.0, trend: "flat" },
    { dimension: "fit", score: 4.0, trend: "up" },
    { dimension: "return_intent", score: 4.5, trend: "up" },
  ],
  started_at: "2026-05-24T00:00:00Z",
  ended_at: "2026-05-24T00:10:00Z",
};

// Per-route empty stubs — list pages whose endpoints have shapes that
// the generic {items:[]} default doesn't match. Each must mirror the
// fields the page reads (.length, .map sites) so empty-state branches
// render without TypeError.
const INTERVIEWS_LIST_EMPTY = { trends: {}, sessions: [] };
const ADMIN_PLATFORM_EMPTY = {
  total_users: 0,
  student_count: 0,
  scholarship_count: 0,
  ingestion_runs_recent: [],
};
const ADMIN_HEALTH_EMPTY = { kpi_alerts: [], db: "ok", version: "stub" };
const CURATION_RECORDS_EMPTY = { items: [], total: 0, page: 1, page_size: 20 };

export const STUDENT_ROUTES = [
  { path: "/feed", name: "feed", auth: "student", states: ["loaded", "error"] },
  { path: "/discover", name: "discover", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/scholarships", name: "match", auth: "student", states: ["loaded", "empty", "error", "locked402"] },
  { path: "/scholarships/1", name: "scholarship-detail", auth: "student", states: ["loaded", "error"] },
  { path: "/dashboard/scholarships/match", name: "match-alias", auth: "student", states: ["loaded"] },
  { path: "/saved", name: "saved", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/tracker", name: "tracker", auth: "student", states: ["loaded", "empty", "error", "locked402"] },
  { path: "/documents", name: "documents", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/documents/sop", name: "documents-sop", auth: "student", states: ["loaded", "locked402"] },
  { path: "/documents/professor-email", name: "documents-prof", auth: "student", states: ["loaded", "locked402"] },
  {
    path: "/interviews",
    name: "interviews",
    auth: "student",
    states: ["loaded", "empty", "error"],
    mock_paths: ["/interviews/coaching-analytics"],
    mock_empty_body: INTERVIEWS_LIST_EMPTY,
  },
  { path: "/interviews/visa", name: "interviews-visa", auth: "student", states: ["loaded", "locked402"] },
  { path: "/profile", name: "profile", auth: "student", states: ["loaded", "error"] },
  { path: "/settings", name: "settings", auth: "student", states: ["loaded"] },
  {
    path: "/documents/1",
    name: "document-detail",
    auth: "student",
    states: ["loaded", "error"],
    mock_paths: ["/documents/1"],
    mock_ok_body: DOCUMENT_DETAIL_STUB,
  },
  {
    path: "/interviews/1",
    name: "interview-detail",
    auth: "student",
    states: ["loaded", "error"],
    mock_paths: ["/interviews/1"],
    mock_ok_body: INTERVIEW_DETAIL_STUB,
  },
];

/**
 * Admin uses admin@example.com (strongpass1). Admin role is included in
 * MENTOR_ROLES + PARTNER_ROLES per frontend/src/lib/auth/RoleGuard.tsx, so
 * the admin token can drive mentor/* and partners/* surfaces too.
 *
 * Dynamic detail routes (admin/curation/1, admin/ingestion/1) assume seed
 * IDs exist. If they 404 the report will surface that.
 */
export const ADMIN_ROUTES = [
  {
    path: "/admin",
    name: "admin-overview",
    auth: "admin",
    states: ["loaded", "error"],
    // /admin page reads both /analytics (platform) and /health (kpi_alerts).
    // Empty stub returns shape that the page expects so .length / .map
    // accesses don't crash on undefined.
    mock_paths: ["/analytics", "/health"],
    mock_empty_body: { ...ADMIN_PLATFORM_EMPTY, ...ADMIN_HEALTH_EMPTY },
  },
  { path: "/admin/ingestion", name: "admin-ingestion", auth: "admin", states: ["loaded", "empty", "error"] },
  { path: "/admin/ingestion/1", name: "admin-ingestion-detail", auth: "admin", states: ["loaded", "error"] },
  {
    path: "/admin/curation",
    name: "admin-curation",
    auth: "admin",
    states: ["loaded", "empty", "error"],
    mock_paths: ["/curation/records"],
    mock_empty_body: CURATION_RECORDS_EMPTY,
  },
  { path: "/admin/curation/1", name: "admin-curation-detail", auth: "admin", states: ["loaded", "error"] },
  { path: "/admin/users", name: "admin-users", auth: "admin", states: ["loaded", "empty", "error"] },
  { path: "/admin/audit", name: "admin-audit", auth: "admin", states: ["loaded", "empty", "error"] },
  { path: "/admin/rec-eval", name: "admin-rec-eval", auth: "admin", states: ["loaded", "error"] },
];

export const MENTOR_ROUTES = [
  { path: "/mentor/queue", name: "mentor-queue", auth: "admin", states: ["loaded", "empty", "error"] },
  {
    path: "/mentor/documents/1",
    name: "mentor-review",
    auth: "admin",
    states: ["loaded", "error"],
    mock_paths: ["/documents/1", "/mentor/documents/1"],
    mock_ok_body: DOCUMENT_DETAIL_STUB,
  },
];

export const PARTNER_ROUTES = [
  { path: "/partners", name: "partners-overview", auth: "admin", states: ["loaded", "error"] },
  { path: "/partners/universities", name: "partners-universities", auth: "admin", states: ["loaded", "empty", "error"] },
];

export const ALL_ROUTES = [
  ...SYSTEM_ROUTES,
  ...PUBLIC_ROUTES,
  ...LEGAL_ROUTES,
  ...STUDENT_ROUTES,
  ...ADMIN_ROUTES,
  ...MENTOR_ROUTES,
  ...PARTNER_ROUTES,
];

export const VIEWPORTS = [
  { name: "375", width: 375, height: 720 },
  { name: "768", width: 768, height: 1024 },
  { name: "1024", width: 1024, height: 800 },
  { name: "1440", width: 1440, height: 900 },
];

/**
 * §7.5 global banned-phrase ledger. Lowercased.
 * Word-boundary matching is applied in copy-grep.mjs so substrings inside
 * legitimate words (e.g. "magical" matches "magic" but not "magnification")
 * are caught while CSS class fragments are not.
 */
export const GLOBAL_BANNED = [
  "unlock",
  "unleash",
  "magical",
  "magic",
  "ai is thinking",
  "ai is generating",
  "powered by ai",
  "revolutionary",
  "game-changing",
  "seamlessly",
  "leverage",
  "synergize",
  "next-generation",
  "world-class",
  "cutting-edge",
  "reimagined",
  "reinvented",
  "effortless",
  "just a moment",
  "hang tight",
  "almost there",
  "hold tight",
  "awesome",
  "oopsy",
  "whoops",
  "uh-oh",
  "naughty",
  "lost in space",
];

/**
 * Banned emoji set (spec §11.6). Used both for source-tree grep and
 * runtime body-text scan.
 */
export const BANNED_EMOJI = ["🚀", "✨", "🎉", "🔥", "⚡", "👋", "🎯", "💪"];
