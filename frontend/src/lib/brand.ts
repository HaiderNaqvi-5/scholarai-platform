/**
 * Brand-level constants. Display brand is "AidwiseAI" (CLAUDE.md). Internal
 * repo identity remains "ScholarAI" — backend `partnerships@scholarai.pk` is
 * the canonical mailbox; the brand rename to `@aidwiseai.pk` is post-cutover.
 *
 * One source of truth: import these instead of hardcoding strings in pages.
 */

export const BRAND_DISPLAY_NAME = "AidwiseAI";

export const PARTNERSHIPS_EMAIL = "partnerships@scholarai.pk";

export const PARTNERSHIPS_MAILTO_HREF =
  `mailto:${PARTNERSHIPS_EMAIL}?subject=${encodeURIComponent("Partnership Inquiry")}`;

/** Per-tier subject lines for the institution CTA. */
export const partnershipsMailto = (subject = "Partnership Inquiry"): string =>
  `mailto:${PARTNERSHIPS_EMAIL}?subject=${encodeURIComponent(subject)}`;
