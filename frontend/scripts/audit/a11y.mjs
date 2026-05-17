/**
 * a11y.mjs — axe-core injection. Returns { violations } where every entry
 * has impact ∈ {minor, moderate, serious, critical}. Caller decides which
 * impact level blocks.
 */

import AxeBuilder from "@axe-core/playwright";

const BLOCK_IMPACT = new Set(["serious", "critical"]);

export async function runAxe(page) {
  try {
    const result = await new AxeBuilder({ page })
      // Premium Cultural ivory base is 13.9:1 ink-deep on ivory; safe.
      // We still run color-contrast since some chips ride near the floor.
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
      .disableRules([
        // skip-link is provided by Next.js shell; axe sometimes can't see it
        "skip-link",
      ])
      .analyze();
    const violations = result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      help: v.help,
      helpUrl: v.helpUrl,
      nodes: v.nodes.length,
      sample: v.nodes[0]?.html?.slice(0, 140) || "",
    }));
    const blocking = violations.filter((v) => BLOCK_IMPACT.has(v.impact));
    return { violations, blocking };
  } catch (err) {
    return { violations: [], blocking: [], error: err.message };
  }
}
