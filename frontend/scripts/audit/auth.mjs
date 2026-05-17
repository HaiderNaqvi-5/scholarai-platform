/**
 * auth.mjs — log in against the live backend, return tokens, and inject
 * them into a Playwright context's localStorage before any page load.
 *
 * Token keys mirror lib/api/client.ts:
 *   grantpath.access_token
 *   grantpath.refresh_token
 *   grantpath.access_expires_at
 */

const API = process.env.AIDWISE_API_BASE_URL || "http://localhost:8000/api/v1";

const CREDS = {
  student: {
    email: process.env.DEMO_STUDENT_EMAIL || "zara.khan@example.com",
    password: process.env.DEMO_STUDENT_PASSWORD || "ScholarAI-Demo-2026!",
  },
  admin: {
    email: process.env.DEMO_ADMIN_EMAIL || "admin@example.com",
    password: process.env.DEMO_ADMIN_PASSWORD || "strongpass1",
  },
};

const tokenCache = new Map();

export async function login(role) {
  if (role === "public") return null;
  if (tokenCache.has(role)) return tokenCache.get(role);

  const creds = CREDS[role];
  if (!creds) throw new Error(`auth: unknown role "${role}"`);

  const resp = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(creds),
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`auth: login failed for ${role} (${resp.status}): ${body.slice(0, 200)}`);
  }
  const data = await resp.json();
  const tokens = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: data.access_expires_at || new Date(Date.now() + 30 * 60 * 1000).toISOString(),
  };
  tokenCache.set(role, tokens);
  return tokens;
}

/**
 * Attach token-injection to a Playwright context. Runs on every navigation
 * so refresh-token rotation is preserved.
 */
export async function attachAuth(context, tokens) {
  if (!tokens) return;
  await context.addInitScript(
    ({ access, refresh, expires }) => {
      try {
        localStorage.setItem("grantpath.access_token", access);
        localStorage.setItem("grantpath.refresh_token", refresh);
        localStorage.setItem("grantpath.access_expires_at", expires);
      } catch {
        // ignore quota / private-mode errors
      }
    },
    { access: tokens.access_token, refresh: tokens.refresh_token, expires: tokens.expires_at },
  );
}
