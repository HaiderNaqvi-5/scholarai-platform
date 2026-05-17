#!/usr/bin/env bun
/**
 * runner.mjs — state-matrix audit. Drives Playwright through:
 *   routes × viewports × states
 *
 * For each cell:
 *   - log in if auth != public
 *   - apply state mock (page.route())
 *   - goto route, wait for load, dismiss CookieBanner via localStorage
 *   - run axe (a11y.mjs), copy-grep (copy-grep.mjs), capture console errors
 *   - screenshot
 * Writes audit-out/REPORT.md + audit-out/summary.json.
 *
 * Usage:
 *   bun scripts/audit/runner.mjs                       # all routes, all states, all viewports
 *   bun scripts/audit/runner.mjs --routes=system       # SYSTEM_ROUTES only
 *   bun scripts/audit/runner.mjs --routes=public,legal
 *   bun scripts/audit/runner.mjs --states=loaded
 *   bun scripts/audit/runner.mjs --viewports=375,1024
 *   bun scripts/audit/runner.mjs --self-test           # synthetic injected ban hit
 */

import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  ALL_ROUTES,
  SYSTEM_ROUTES,
  PUBLIC_ROUTES,
  LEGAL_ROUTES,
  STUDENT_ROUTES,
  VIEWPORTS,
} from "./routes.mjs";
import { login, attachAuth } from "./auth.mjs";
import { runAxe } from "./a11y.mjs";
import { scanCopy } from "./copy-grep.mjs";
import { mock402, mockError, mockEmpty, mockLoading, endpointsFor } from "./state-mock.mjs";
import { writeReport, verdictOf } from "./report.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../audit-out");
const BASE = process.env.AIDWISE_BASE_URL || "http://localhost:3000";

function parseArgs(argv) {
  const opts = { routes: null, states: null, viewports: null, selfTest: false };
  for (const a of argv) {
    if (a.startsWith("--routes=")) opts.routes = a.slice(9).split(",");
    else if (a.startsWith("--states=")) opts.states = a.slice(9).split(",");
    else if (a.startsWith("--viewports=")) opts.viewports = a.slice(12).split(",");
    else if (a === "--self-test") opts.selfTest = true;
  }
  return opts;
}

function pickRoutes(filter) {
  if (!filter) return ALL_ROUTES;
  const sets = {
    system: SYSTEM_ROUTES,
    public: PUBLIC_ROUTES,
    legal: LEGAL_ROUTES,
    student: STUDENT_ROUTES,
    all: ALL_ROUTES,
  };
  const out = [];
  for (const tag of filter) {
    if (sets[tag]) out.push(...sets[tag]);
    else out.push(...ALL_ROUTES.filter((r) => r.path === tag || r.name === tag));
  }
  return out;
}

function pickViewports(filter) {
  if (!filter) return VIEWPORTS;
  return VIEWPORTS.filter((v) => filter.includes(v.name));
}

async function dismissCookie(page) {
  await page.evaluate(() => {
    try {
      localStorage.setItem(
        "aidwise.cookie_consent",
        JSON.stringify({
          essential: true,
          analytics: false,
          marketing: false,
          b2b: false,
          agreed_at: new Date().toISOString(),
        }),
      );
    } catch {
      // ignore
    }
  });
}

async function applyStateMock(page, route, state) {
  const endpoints = route.mock_paths || endpointsFor(route.path);
  if (endpoints.length === 0) return;
  switch (state) {
    case "locked402":
      await mock402(page, endpoints);
      break;
    case "error":
      await mockError(page, endpoints, 500);
      break;
    case "empty":
      await mockEmpty(page, endpoints);
      break;
    case "loading":
      await mockLoading(page, endpoints, 4000);
      break;
    default:
      break;
  }
}

async function runCell(browser, route, vp, state, tokens) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  await attachAuth(ctx, tokens);
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => pageErrors.push(err.message));

  await applyStateMock(page, route, state);

  const url = `${BASE}${route.path}`;
  const start = Date.now();
  let status = 0;
  let title = "";
  try {
    const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
    status = resp ? resp.status() : 0;
    await dismissCookie(page);
    // Wait for paint to settle; loading state intentionally captures mid-skeleton.
    if (state !== "loading") {
      await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
    } else {
      await page.waitForTimeout(800);
    }
    title = await page.title().catch(() => "");
  } catch (e) {
    consoleErrors.push(`goto failed: ${e.message}`);
  }

  const a11y = await runAxe(page);
  const copy = await scanCopy(page, route);

  const shotPath = `${OUT}/${route.name}-${state}-${vp.name}.png`;
  try {
    await page.screenshot({ path: shotPath, fullPage: true });
  } catch (e) {
    consoleErrors.push(`screenshot failed: ${e.message}`);
  }

  await ctx.close();
  const entry = {
    route: route.path,
    name: route.name,
    viewport: vp.name,
    state,
    status,
    title,
    a11y,
    copy,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    time_ms: Date.now() - start,
    screenshot: shotPath,
  };
  entry.verdict = verdictOf(entry);
  return entry;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const routes = pickRoutes(opts.routes);
  const viewports = pickViewports(opts.viewports);
  await mkdir(OUT, { recursive: true });

  // Pre-flight: log in for any non-public auth role we'll need.
  const roles = [...new Set(routes.map((r) => r.auth))].filter((r) => r !== "public");
  const roleTokens = {};
  for (const role of roles) {
    try {
      roleTokens[role] = await login(role);
      console.log(`[auth] logged in as ${role}`);
    } catch (e) {
      console.error(`[auth] ${e.message}`);
      console.error(`[auth] continuing — student routes will likely fail`);
      roleTokens[role] = null;
    }
  }

  const browser = await chromium.launch({
    timeout: 60_000,
    headless: true,
    args: ["--disable-dev-shm-usage", "--no-sandbox"],
  });

  const results = [];
  for (const route of routes) {
    const states = (opts.states ? opts.states.filter((s) => route.states.includes(s)) : route.states)
      .filter(Boolean);
    if (states.length === 0) continue;
    for (const state of states) {
      for (const vp of viewports) {
        const tokens = route.auth !== "public" ? roleTokens[route.auth] : null;
        const entry = await runCell(browser, route, vp, state, tokens);
        results.push(entry);
        const ok = entry.verdict === "PASS" ? "✓" : entry.verdict === "WARN" ? "·" : "✗";
        console.log(
          `${ok} ${vp.name.padStart(4)}  ${state.padEnd(10)}  ${route.path.padEnd(36)}  ${entry.status} a11y=${entry.a11y?.blocking?.length || 0} copy=${(entry.copy?.phrase_hits?.length || 0) + (entry.copy?.emoji_hits?.length || 0)} con=${entry.console_errors.length + entry.page_errors.length}`,
        );
      }
    }
  }

  // Self-test: inject a known ban into a synthetic result.
  if (opts.selfTest) {
    const synth = {
      route: "/__self_test__",
      name: "self-test",
      viewport: "1024",
      state: "loaded",
      status: 200,
      a11y: { violations: [], blocking: [] },
      copy: { phrase_hits: [{ phrase: "unlock", line: "Synthetic unlock injected" }], emoji_hits: [] },
      console_errors: [],
      page_errors: [],
      time_ms: 0,
      screenshot: null,
    };
    synth.verdict = verdictOf(synth);
    results.push(synth);
    if (synth.verdict !== "FAIL") {
      console.error("[self-test] FAILED — verdict should have been FAIL");
      process.exit(2);
    }
    console.log("[self-test] OK — injected ban produced FAIL verdict");
  }

  await browser.close();

  const meta = {
    base: BASE,
    generated_at: new Date().toISOString(),
    auth_roles: roles,
    route_count: routes.length,
    viewports: viewports.map((v) => v.name),
    states: opts.states || ["loaded", "empty", "loading", "processing", "error", "locked402"],
  };
  await writeFile(`${OUT}/summary.json`, JSON.stringify({ meta, results }, null, 2), "utf8");
  await writeReport(`${OUT}/REPORT.md`, results, meta);

  const fails = results.filter((r) => r.verdict === "FAIL").length;
  const warns = results.filter((r) => r.verdict === "WARN").length;
  console.log(`\n${results.length} cells  ·  ${fails} FAIL  ·  ${warns} WARN`);
  console.log(`Wrote ${OUT}/REPORT.md + summary.json`);
  if (fails > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
