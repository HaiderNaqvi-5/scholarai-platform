# ScholarAI Frontend

This is the active Next.js frontend for the ScholarAI MVP.

## Local run
1. Copy `.env.local.example` to `.env.local`.
2. Run `npm ci`.
3. Run `npm run dev`.
4. Open `http://localhost:3000`.

## Sanity commands
- `npm run lint`
- `npm run typecheck`
- `npm run build`

## Notes
- The frontend expects the backend API at `NEXT_PUBLIC_API_BASE_URL`.
- Protected workspace routes depend on the token-backed auth provider in `src/components/auth/`.
- UI direction is governed by `docs/scholarai/03_brand_and_design_system.md`.
