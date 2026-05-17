/**
 * copy-grep.mjs — extract document.body.innerText and grep for banned
 * phrases. Token boundaries enforced via regex to avoid catching
 * substrings inside legitimate words (e.g. "magical" matches "magic"
 * via word-boundary; "magnification" does not).
 *
 * Emoji scan uses raw inclusion since emoji are not part of word chars.
 *
 * Allowlist: per-route `expected_phrases` silences known-good hits.
 */

import { GLOBAL_BANNED, BANNED_EMOJI } from "./routes.mjs";

function buildPattern(phrase) {
  // Escape regex metachars, then apply word-boundary on both sides.
  const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`\\b${escaped}\\b`, "i");
}

export async function scanCopy(page, route) {
  const text = await page.evaluate(() => document.body?.innerText || "");
  const lowered = text.toLowerCase();
  const allowed = new Set((route.expected_phrases || []).map((p) => p.toLowerCase()));
  const lexicon = [...GLOBAL_BANNED, ...(route.banned_extra || [])];

  const phraseHits = [];
  for (const phrase of lexicon) {
    if (allowed.has(phrase)) continue;
    if (buildPattern(phrase).test(text)) {
      // Capture the line containing the hit for context.
      const lines = text.split(/\r?\n/);
      const idx = lines.findIndex((line) => buildPattern(phrase).test(line));
      phraseHits.push({
        phrase,
        line: idx >= 0 ? lines[idx].trim().slice(0, 140) : "",
      });
    }
  }

  const emojiHits = [];
  for (const e of BANNED_EMOJI) {
    if (text.includes(e)) emojiHits.push(e);
  }

  // Length-only sanity log; not blocking.
  return {
    body_chars: lowered.length,
    phrase_hits: phraseHits,
    emoji_hits: emojiHits,
  };
}
