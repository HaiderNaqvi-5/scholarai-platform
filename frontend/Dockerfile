# Frontend Dockerfile (S11 hardened).
# Bun is the canonical package manager per frontend/CLAUDE.md.
# Multi-stage: builder produces the .next standalone, runner ships the
# minimal node + standalone output as non-root.

FROM oven/bun:1-alpine AS builder

WORKDIR /app

# Copy lockfile first for layer cache. --frozen-lockfile pins exact deps
# (supply-chain hygiene; refuses install when bun.lock + package.json
# disagree).
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

# ── Runtime ─────────────────────────────────────────────────────────────
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    NEXT_TELEMETRY_DISABLED=1

# wget is the smallest tool that ships in alpine for HEALTHCHECK.
# Drop apk caches to keep the runtime layer thin.
RUN apk add --no-cache wget tini \
    && addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy only what the production server needs. Excludes devDeps + source.
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

USER nextjs

EXPOSE 3000

# tini reaps zombie processes for SIGTERM-clean shutdowns under docker stop.
ENTRYPOINT ["/sbin/tini", "--"]

# S11 — liveness probe so docker swarm / compose can flag a hung Node
# without restarting on every benign 4xx. `next start` answers / with 200
# once the server is ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/ >/dev/null 2>&1 || exit 1

CMD ["node_modules/.bin/next", "start"]
