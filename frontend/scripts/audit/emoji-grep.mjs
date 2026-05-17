#!/usr/bin/env bun
/**
 * emoji-grep.mjs — source-tree scan for banned emoji in JSX/TSX. Run as a
 * fast pre-flight gate (no browser needed). Exit 1 on any hit.
 *
 * Run: bun scripts/audit/emoji-grep.mjs
 */

import { readdir, readFile, stat } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { BANNED_EMOJI } from "./routes.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "../../src");

// Allow emoji inside code comments only (rare; flag everywhere for safety).
const EXTS = new Set([".tsx", ".ts", ".jsx", ".js", ".css", ".md"]);
const SKIP_DIRS = new Set(["node_modules", ".next", "audit-out", "build", "dist"]);

const pattern = new RegExp(`[${BANNED_EMOJI.join("")}]`, "u");

async function walk(dir, acc) {
  const entries = await readdir(dir);
  for (const name of entries) {
    if (SKIP_DIRS.has(name)) continue;
    const p = join(dir, name);
    const s = await stat(p);
    if (s.isDirectory()) {
      await walk(p, acc);
    } else if (EXTS.has(p.slice(p.lastIndexOf(".")))) {
      acc.push(p);
    }
  }
  return acc;
}

// Lines that are clearly inside a /* ... */ block comment (start with
// optional whitespace + `*`) are documentation of bans, not shipped UI.
// Also skip `//` line comments and lines containing `Banned:` / `Per-screen bans:`.
const COMMENT_LINE = /^\s*(\*|\/\/)/;
const BAN_DOC = /(Banned\b|Per-screen bans:|emoji-as-UI|banned set)/i;

const hits = [];
const files = await walk(ROOT, []);
for (const f of files) {
  const body = await readFile(f, "utf8");
  const lines = body.split(/\r?\n/);
  lines.forEach((line, i) => {
    if (!pattern.test(line)) return;
    if (COMMENT_LINE.test(line)) return;
    if (BAN_DOC.test(line)) return;
    hits.push({ file: f.replace(ROOT, "src"), line: i + 1, text: line.trim().slice(0, 160) });
  });
}

if (hits.length === 0) {
  console.log(`[OK] emoji-grep: 0 banned emoji across ${files.length} files`);
  process.exit(0);
} else {
  console.error(`[FAIL] emoji-grep: ${hits.length} banned emoji hits`);
  for (const h of hits) console.error(`  ${h.file}:${h.line}  ${h.text}`);
  process.exit(1);
}
