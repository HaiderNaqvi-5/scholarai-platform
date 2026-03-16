# ScholarAI Frontend

This is the active Next.js frontend for the ScholarAI MVP.

## Local run
1. Copy `.env.local.example` to `.env.local`.
2. Run `npm ci`.
3. Make sure the backend is available at `NEXT_PUBLIC_API_BASE_URL`.
4. Run `npm run dev`.
5. Open `http://localhost:3000`.

## Restart note
- If route files or app-structure files changed while the frontend dev server was already running, restart `npm run dev`. A stale Next.js process can serve false `404` responses for newly added pages.

## Sanity commands
- `npm run lint`
- `npm run typecheck`
- `npm run build`

## Notes
- The frontend expects the backend API at `NEXT_PUBLIC_API_BASE_URL`.
- Protected workspace routes depend on the token-backed auth provider in `src/components/auth/`.
- UI direction is governed by `docs/scholarai/03_brand_and_design_system.md`.
