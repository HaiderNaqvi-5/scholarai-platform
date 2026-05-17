/**
 * state-mock.mjs — Playwright route() helpers for state-matrix coverage.
 *
 * Each helper installs a request interceptor for the matching API path.
 * Removed by calling page.unroute(pattern) before the next state, or by
 * disposing the context (runner does this between states).
 */

const API_PREFIX = "**/api/v1";

/** 402 plan-required, matches lib/api/client.ts isPlanRequiredError */
export async function mock402(page, paths) {
  for (const p of paths) {
    await page.route(`${API_PREFIX}${p}`, (route) =>
      route.fulfill({
        status: 402,
        contentType: "application/json",
        body: JSON.stringify({
          detail: {
            code: "plan_required",
            message: "See all matches with Pro (PKR 2,999/mo).",
            required_plan: "pro",
            current_plan: "free",
            price: 2999,
            currency: "PKR",
          },
        }),
      }),
    );
  }
}

/** 500 server error on listed paths */
export async function mockError(page, paths, status = 500) {
  for (const p of paths) {
    await page.route(`${API_PREFIX}${p}`, (route) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "internal_error", message: "Unavailable." } }),
      }),
    );
  }
}

/** Empty list payload. Server returns 200 with [] or {items:[], total:0}. */
export async function mockEmpty(page, paths) {
  for (const p of paths) {
    await page.route(`${API_PREFIX}${p}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, results: [], unlock_offer: null }),
      }),
    );
  }
}

/** Stall the response 5s so the loading skeleton is captured. */
export async function mockLoading(page, paths, delayMs = 5000) {
  for (const p of paths) {
    await page.route(`${API_PREFIX}${p}`, async (route) => {
      await new Promise((r) => setTimeout(r, delayMs));
      route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    });
  }
}

/**
 * Per-route default endpoint mapping. The runner picks the right set
 * based on the route's `path`. Override by adding `mock_paths` in the
 * route manifest.
 */
export const PRIMARY_ENDPOINTS = {
  "/feed": ["/recommendations", "/tracker/summary", "/profile/me"],
  "/discover": ["/scholarships"],
  "/scholarships": ["/scholarships/match"],
  "/scholarships/*": ["/scholarships/*"],
  "/saved": ["/saved-opportunities"],
  "/tracker": ["/tracker"],
  "/documents": ["/documents"],
  "/documents/sop": ["/documents/sop/draft"],
  "/documents/professor-email": ["/documents/professor-email"],
  "/interviews": ["/interviews"],
  "/interviews/visa": ["/interviews/visa/start"],
  "/profile": ["/profile/me"],
  "/settings": ["/auth/me"],
  "/legal/*": ["/privacy/legal/*"],
};

export function endpointsFor(routePath) {
  if (PRIMARY_ENDPOINTS[routePath]) return PRIMARY_ENDPOINTS[routePath];
  // Wildcard match: try the longest prefix-match
  const prefixed = Object.keys(PRIMARY_ENDPOINTS)
    .filter((k) => k.endsWith("/*"))
    .find((k) => routePath.startsWith(k.slice(0, -2)));
  return prefixed ? PRIMARY_ENDPOINTS[prefixed] : [];
}
