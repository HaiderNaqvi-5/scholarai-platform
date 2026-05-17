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

export const STUDENT_ROUTES = [
  { path: "/feed", name: "feed", auth: "student", states: ["loaded", "error"] },
  { path: "/discover", name: "discover", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/scholarships", name: "match", auth: "student", states: ["loaded", "empty", "error", "locked402"] },
  { path: "/scholarships/1", name: "scholarship-detail", auth: "student", states: ["loaded", "error"] },
  { path: "/saved", name: "saved", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/tracker", name: "tracker", auth: "student", states: ["loaded", "empty", "error", "locked402"] },
  { path: "/documents", name: "documents", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/documents/sop", name: "documents-sop", auth: "student", states: ["loaded", "locked402"] },
  { path: "/documents/professor-email", name: "documents-prof", auth: "student", states: ["loaded", "locked402"] },
  { path: "/interviews", name: "interviews", auth: "student", states: ["loaded", "empty", "error"] },
  { path: "/interviews/visa", name: "interviews-visa", auth: "student", states: ["loaded", "locked402"] },
  { path: "/profile", name: "profile", auth: "student", states: ["loaded", "error"] },
  { path: "/settings", name: "settings", auth: "student", states: ["loaded"] },
];

export const ALL_ROUTES = [
  ...SYSTEM_ROUTES,
  ...PUBLIC_ROUTES,
  ...LEGAL_ROUTES,
  ...STUDENT_ROUTES,
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
