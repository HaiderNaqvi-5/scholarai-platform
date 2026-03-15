import { MarketingShell } from "@/components/layout/marketing-shell";
import { StatusBadge } from "@/components/ui/status-badge";
import { appRoutes } from "@/lib/routes";

export default function LandingPage() {
  return (
    <MarketingShell
      eyebrow="Canada-first scholarship guidance"
      title="ScholarAI helps students move from scattered research to confident application planning."
      description="A restrained, data-first MVP for scholarship discovery, eligibility-aware recommendations, document feedback, and interview practice."
    >
      <section className="hero-grid">
        <article className="surface-card">
          <p className="section-eyebrow">Why this MVP exists</p>
          <h2 className="section-title">Structured facts first, guidance second.</h2>
          <p className="body-copy">
            ScholarAI treats validated scholarship records as the source of truth,
            then layers recommendations and preparation support on top.
          </p>
        </article>
        <article className="surface-panel">
          <p className="section-eyebrow">Core paths</p>
          <ul className="stack-list">
            <li>Discover scholarships in a Canada-first corpus</li>
            <li>Review eligibility-aware recommendation lists</li>
            <li>Improve documents with grounded feedback</li>
            <li>Practice interviews with rubric-based guidance</li>
          </ul>
        </article>
      </section>
      <section className="surface-card">
        <p className="section-eyebrow">Foundation routes</p>
        <div className="route-grid">
          {appRoutes.slice(1).map((route) => (
            <article className="route-card" key={route.href}>
              <div className="meta-row">
                <StatusBadge
                  label={route.status === "next" ? "Next slice" : route.status}
                  variant={route.status === "deferred" ? "warning" : "planned"}
                />
              </div>
              <h3 className="route-card__title">{route.label}</h3>
              <p className="route-card__description">{route.description}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="split-panel">
        <article className="data-callout">
          <p className="list-label">Validated data</p>
          <p className="body-copy">
            Published scholarship records, eligibility constraints, and
            provenance-aware fields remain the authority for user-facing facts.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Generated guidance</p>
          <p className="body-copy">
            Recommendations, document feedback, and interview support remain
            bounded overlays on top of validated data, not replacements for it.
          </p>
        </article>
      </section>
    </MarketingShell>
  );
}
