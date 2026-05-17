#!/usr/bin/env bun
/**
 * visual-audit.mjs — Playwright pass over the Premium Cultural rebuild.
 *
 * Visits every public-facing route at three breakpoints (375 / 1024 / 1440),
 * captures a screenshot, records any console errors, and writes a JSON +
 * markdown digest to ./audit-out/.
 *
 * Run: `bunx playwright install chromium` (one-time) then
 *      `bun scripts/visual-audit.mjs`
 *
 * The script does NOT block — it logs failures and continues so a single
 * stale route doesn't kill the whole sweep. The summary at the end lists
 * any non-200 status, console error, or page-error event.
 */

import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.AIDWISE_BASE_URL || "http://localhost:3000";
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../audit-out");

/** Routes that don't require authentication. */
const PUBLIC_ROUTES = [
  { path: "/", name: "landing" },
  { path: "/booth/air-university", name: "booth" },
  { path: "/upgrade", name: "pricing" },
  { path: "/signup", name: "signup" },
  { path: "/signup?invite=AIRU2026", name: "signup-airu" },
  { path: "/login", name: "login" },
  { path: "/legal/privacy", name: "legal-privacy" },
  { path: "/universities", name: "universities" },
];

const VIEWPORTS = [
  { name: "375", width: 375, height: 720 },
  { name: "1024", width: 1024, height: 800 },
  { name: "1440", width: 1440, height: 900 },
];

async function main() {
  await mkdir(OUT, { recursive: true });

  // First-launch on Windows can pause for Defender; allow extra time.
  const browser = await chromium.launch({
    timeout: 60_000,
    headless: true,
    args: ["--disable-dev-shm-usage", "--no-sandbox"],
  });
  const results = [];

  for (const route of PUBLIC_ROUTES) {
    for (const vp of VIEWPORTS) {
      const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await ctx.newPage();
      const consoleErrors = [];
      const pageErrors = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      });
      page.on("pageerror", (err) => pageErrors.push(err.message));

      const url = `${BASE}${route.path}`;
      const start = Date.now();
      let status = 0;
      let title = "";
      try {
        const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
        status = resp ? resp.status() : 0;
        title = await page.title().catch(() => "");
        // Skip the cookie banner so it doesn't cover screenshots.
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
        await page.reload({ waitUntil: "networkidle", timeout: 30_000 });
        await page.waitForTimeout(400);
      } catch (e) {
        consoleErrors.push(`goto failed: ${e.message}`);
      }

      const shotPath = `${OUT}/${route.name}-${vp.name}.png`;
      try {
        await page.screenshot({ path: shotPath, fullPage: true });
      } catch (e) {
        consoleErrors.push(`screenshot failed: ${e.message}`);
      }

      results.push({
        route: route.path,
        name: route.name,
        viewport: vp.name,
        status,
        title,
        time_ms: Date.now() - start,
        consoleErrors,
        pageErrors,
        screenshot: shotPath,
      });
      await ctx.close();
      const tag = status === 200 ? "OK " : "ERR";
      const errCount = consoleErrors.length + pageErrors.length;
      console.log(
        `[${tag}] ${vp.name.padStart(4)}  ${route.path.padEnd(36)}  ${status} ${errCount ? `· ${errCount} errors` : ""}`,
      );
    }
  }

  await browser.close();

  // Per-route summary
  const summary = {
    base: BASE,
    generated_at: new Date().toISOString(),
    total: results.length,
    failures: results.filter((r) => r.status !== 200).length,
    console_error_routes: results.filter((r) => r.consoleErrors.length > 0).map((r) => `${r.name}-${r.viewport}`),
    page_error_routes: results.filter((r) => r.pageErrors.length > 0).map((r) => `${r.name}-${r.viewport}`),
    results,
  };

  await writeFile(`${OUT}/summary.json`, JSON.stringify(summary, null, 2));

  const md = [
    `# AidwiseAI visual audit — ${summary.generated_at}`,
    ``,
    `Base: ${BASE}`,
    `Routes audited: ${summary.total / VIEWPORTS.length} · Viewports: ${VIEWPORTS.map((v) => v.name).join(" / ")}`,
    `Failures: ${summary.failures} · Console errors: ${summary.console_error_routes.length} · Page errors: ${summary.page_error_routes.length}`,
    ``,
    `| Status | Viewport | Route | Title | Errors | ms |`,
    `|--------|----------|-------|-------|--------|----|`,
    ...results.map(
      (r) =>
        `| ${r.status === 200 ? "✅" : "❌ " + r.status} | ${r.viewport} | \`${r.route}\` | ${r.title || "—"} | ${r.consoleErrors.length + r.pageErrors.length} | ${r.time_ms} |`,
    ),
    ``,
    `## Console / page errors`,
    ``,
    ...results
      .filter((r) => r.consoleErrors.length > 0 || r.pageErrors.length > 0)
      .flatMap((r) => [
        `### \`${r.route}\` @ ${r.viewport}`,
        ...r.consoleErrors.map((e) => `- console: ${e}`),
        ...r.pageErrors.map((e) => `- page: ${e}`),
        ``,
      ]),
  ].join("\n");

  await writeFile(`${OUT}/SUMMARY.md`, md);

  console.log(`\nWrote ${OUT}/summary.json + SUMMARY.md (${summary.failures} failures)`);
  if (summary.failures > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
