# DigitalOcean App Platform — AidwiseAI backend

Deploy spec for the Air-University May-19 trial launch. 3 services + 1 pre-deploy job from a single image.

## Topology

| Component | DO size | $/mo | Notes |
|---|---|---:|---|
| `web` (uvicorn) | basic-xxs (512MB) | $5 | `/livez` health check |
| `celery-worker` | basic-xxs (512MB) | $5 | Bump to basic-xs ($10) once scraper enabled — Chromium needs ~500MB |
| `celery-beat` | basic-xxs (512MB) | $5 | scheduler only, tiny |
| `alembic-migrate` (PRE_DEPLOY job) | basic-xxs | $0 (one-shot) | Runs `alembic upgrade head` before each deploy |
| **Total** | | **$15/mo** | $200 Student Pack credit ≈ 13 months runway |

External managed services (NOT on DO):
- Postgres + pgvector → **Supabase** (ap-south-1 / Mumbai, free tier 500MB)
- Redis → **Upstash** (ap-south-1, free tier 10k cmd/day)
- Email → **Mailgun** (Student Pack 20k/mo)
- Errors → **Sentry Developer** (Student Pack 100k events/mo)
- DNS → **Cloudflare**
- Frontend → **Vercel**

## One-time setup

```powershell
# 1. Install doctl
winget install DigitalOcean.Doctl
# or: scoop install doctl

# 2. Generate API token at https://cloud.digitalocean.com/account/api/tokens
#    scope: read + write. Copy into next command.
doctl auth init

# 3. Verify credit applied (should show "$200.00" remaining)
doctl balance get

# 4. Create the app from spec
doctl apps create --spec .do/app.yaml
# returns: App ID (save it) + default *.ondigitalocean.app URL
```

## Set secrets (after first `create`)

The spec puts `REPLACE_AT_DEPLOY` placeholders for every secret. Fill them in once via the dashboard or CLI. Worker + beat reference `${web.X}` so you only set them on `web`.

```powershell
# Get the app id
doctl apps list

# Per-key update (replace APP_ID + values):
doctl apps update APP_ID --spec .do/app.yaml
# OR set via UI: Apps → aidwiseai-backend → Settings → web → Environment Variables
```

Secret values to set:

| Key | Source |
|---|---|
| `DATABASE_URL` | Supabase → Settings → Database → Connection string (URI mode, **pooler** port 6543, append `?sslmode=require&statement_cache_size=0`) — `postgresql+asyncpg://...` |
| `REDIS_URL` | Upstash console → Redis → "Connect to your database" → TLS endpoint `rediss://default:PASS@host:6379` |
| `CELERY_BROKER_URL` | Same as `REDIS_URL` (or `REDIS_URL/1` for namespace isolation) |
| `CELERY_RESULT_BACKEND` | Same as broker |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` (min 32 chars) |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API keys. Set monthly burn cap = $30 in Anthropic dashboard |
| `MAILGUN_API_KEY` | Mailgun → Settings → API keys → Private API key |
| `MAILGUN_DOMAIN` | `mg.aidwiseai.com` |
| `SENTRY_DSN` | Sentry → aidwiseai-backend project → Settings → Client Keys (DSN) |

## Post-create checklist

- [ ] Verify `alembic-migrate` PRE_DEPLOY job ran clean: `doctl apps logs APP_ID --type build --component alembic-migrate`
- [ ] `web` health check passing: `curl https://<app>.ondigitalocean.app/livez` → 200
- [ ] Seed invite codes against prod DB:
      `DATABASE_URL='...supabase...' python backend/scripts/seed_invite_codes.py`
- [ ] Sentry events flowing: trigger a 5xx on `/api/v1/health` (force) → see in Sentry
- [ ] Mailgun delivering: register a test user → check inbox for welcome
- [ ] Map custom domain: Apps → Settings → Domains → add `api.aidwiseai.com` (CNAME via Cloudflare)
- [ ] Update Vercel `NEXT_PUBLIC_API_BASE_URL` to `https://api.aidwiseai.com/api/v1`

## Ongoing ops

```powershell
# Tail logs (web)
doctl apps logs APP_ID --type run --component web --follow

# Trigger deploy without push
doctl apps create-deployment APP_ID

# Update spec
doctl apps update APP_ID --spec .do/app.yaml

# Rollback
doctl apps list-deployments APP_ID
doctl apps create-deployment APP_ID --force-rebuild=false --rollback-to <deploy-id>
```

## Known constraints

1. **Image size ~1.2GB** (Playwright + Chromium + ML libs). DO build cache mitigates; first build ~12 min, incrementals ~3 min.
2. **No Neo4j / OpenSearch on DO.** Backend imports gracefully degrade — `app.services` falls back when graph + search clients fail to connect. Leave `NEO4J_URI` / OpenSearch env unset; do NOT point at localhost.
3. **Supabase pooler quirk** — `?statement_cache_size=0` REQUIRED on pgbouncer-pooler URLs or asyncpg blows up on prepared statements. Same fix used in dev (see `CLAUDE.md` "Dev env notes 2026-05-12").
4. **Worker OOM risk** — once the scraper Celery queue is enabled, bump `celery-worker` to `basic-xs` (1GB). Chromium + sentence-transformers + lxml together push past 512MB.
5. **PRE_DEPLOY job runs on every deploy.** If a migration is irreversible, the deploy will fail at that step (good — blocks bad code shipping).
