#!/usr/bin/env bun
/**
 * visual-audit.mjs — backwards-compatible wrapper. Delegates to the
 * state-matrix runner with the public-routes preset. Retained so existing
 * CI invocations + the audit-out/ contract stay stable.
 *
 * For full coverage (auth + states), call scripts/audit/runner.mjs directly
 * or use `bun run audit`.
 */

import("./audit/runner.mjs");
// runner reads process.argv; pass-through happens automatically when there
// are no extra args. To run public-only sweep:
//   bun scripts/visual-audit.mjs --routes=public,system,legal
