/**
 * report.mjs — write audit-out/REPORT.md from runner results.
 *
 * Result shape (one entry per route × viewport × state):
 *   {
 *     route, name, viewport, state, status, title, screenshot,
 *     a11y: { violations[], blocking[] },
 *     copy: { phrase_hits[], emoji_hits[], body_chars },
 *     console_errors[], page_errors[], time_ms,
 *     verdict: "PASS" | "WARN" | "FAIL"
 *   }
 */

import { writeFile } from "node:fs/promises";

export function verdictOf(entry) {
  if (entry.status && entry.status >= 500) return "FAIL";
  if (entry.a11y?.blocking?.length > 0) return "FAIL";
  if (entry.copy?.phrase_hits?.length > 0) return "FAIL";
  if (entry.copy?.emoji_hits?.length > 0) return "FAIL";
  if (entry.page_errors?.length > 0) return "FAIL";
  if (entry.console_errors?.length > 0) return "WARN";
  if (entry.status && entry.status >= 400 && entry.status < 500) return "WARN";
  return "PASS";
}

const ICONS = { PASS: "✅", WARN: "⚠️ ", FAIL: "❌" };

export async function writeReport(outPath, results, meta) {
  const lines = [];
  lines.push(`# AidwiseAI audit report — ${meta.generated_at}`);
  lines.push("");
  lines.push(`Base: ${meta.base}  ·  Auth users: ${meta.auth_roles.join(", ") || "—"}`);
  lines.push(
    `Routes: ${meta.route_count}  ·  Viewports: ${meta.viewports.join(" / ")}  ·  States: ${meta.states.join(" / ")}`,
  );
  lines.push("");
  const pass = results.filter((r) => r.verdict === "PASS").length;
  const warn = results.filter((r) => r.verdict === "WARN").length;
  const fail = results.filter((r) => r.verdict === "FAIL").length;
  lines.push(
    `**${pass} pass · ${warn} warn · ${fail} fail** of ${results.length} cells`,
  );
  lines.push("");

  lines.push("## Matrix");
  lines.push("");
  lines.push("| Route | State | Viewport | Status | a11y | Copy | Console | Verdict |");
  lines.push("|-------|-------|----------|--------|------|------|---------|---------|");
  for (const r of results) {
    const a11y = r.a11y?.blocking?.length ? `❌ ${r.a11y.blocking.length}` : `${r.a11y?.violations?.length || 0}`;
    const copy = (r.copy?.phrase_hits?.length || 0) + (r.copy?.emoji_hits?.length || 0);
    const con = (r.console_errors?.length || 0) + (r.page_errors?.length || 0);
    lines.push(
      `| \`${r.route}\` | ${r.state} | ${r.viewport} | ${r.status || "—"} | ${a11y} | ${copy} | ${con} | ${ICONS[r.verdict] || "?"} ${r.verdict} |`,
    );
  }
  lines.push("");

  const fails = results.filter((r) => r.verdict !== "PASS");
  if (fails.length > 0) {
    lines.push("## Failures + warnings — detail");
    lines.push("");
    for (const r of fails) {
      lines.push(`### \`${r.route}\` @ ${r.viewport}  · state=${r.state}  · ${r.verdict}`);
      if (r.status) lines.push(`- HTTP ${r.status}`);
      if (r.a11y?.blocking?.length) {
        lines.push(`- **a11y serious/critical:**`);
        for (const v of r.a11y.blocking) {
          lines.push(`  - ${v.id} (${v.impact}, ${v.nodes} nodes) — ${v.help}`);
        }
      }
      if (r.copy?.phrase_hits?.length) {
        lines.push(`- **banned phrases:**`);
        for (const h of r.copy.phrase_hits) {
          lines.push(`  - \`${h.phrase}\` — ${h.line || "—"}`);
        }
      }
      if (r.copy?.emoji_hits?.length) lines.push(`- **emoji:** ${r.copy.emoji_hits.join(" ")}`);
      if (r.console_errors?.length) {
        lines.push(`- **console errors:**`);
        for (const e of r.console_errors.slice(0, 5)) lines.push(`  - ${e.slice(0, 200)}`);
      }
      if (r.page_errors?.length) {
        lines.push(`- **page errors:**`);
        for (const e of r.page_errors.slice(0, 5)) lines.push(`  - ${e.slice(0, 200)}`);
      }
      lines.push(`- screenshot: \`${r.screenshot || "—"}\``);
      lines.push("");
    }
  }

  await writeFile(outPath, lines.join("\n"), "utf8");
}
