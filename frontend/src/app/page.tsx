import Link from "next/link";

import { MarketingShell } from "@/components/layout/marketing-shell";
import { StatusBadge } from "@/components/ui/status-badge";
import { landingFeatureRoutes } from "@/lib/routes";

export default function LandingPage() {
  return (
    <MarketingShell
      eyebrow="Canada-first scholarship planning"
      title="ScholarAI brings scholarship research, fit, and preparation into one clear workflow."
      description="Structured scholarship facts stay in front. Recommendations and preparation guidance stay visible, bounded, and easy to trust."
      actions={
        <>
          <Link className="auth-link auth-link--primary" href="/scholarships">
            Browse scholarships
          </Link>
          <Link className="nav-link" href="/signup">
            Create account
          </Link>
        </>
      }
    >
      <section className="landing-hero">
        <div className="hero-trust-rail">
          <article className="data-point">
            <p className="data-point__label">Corpus</p>
            <strong>Canada-first, MS-focused</strong>
            <p className="body-copy">
              The MVP stays intentionally narrow around Data Science, AI, and Analytics.
            </p>
          </article>
          <article className="data-point">
            <p className="data-point__label">Trust model</p>
            <strong>Validated facts lead</strong>
            <p className="body-copy">
              Requirements, deadlines, and funding details come from published records.
            </p>
          </article>
          <article className="data-point">
            <p className="data-point__label">Guidance model</p>
            <strong>Advice stays bounded</strong>
            <p className="body-copy">
              Recommendations, writing help, and interview practice are clearly advisory.
            </p>
          </article>
        </div>
      </section>

      <section className="feature-grid" id="how-it-works">
        <article className="surface-card">
          <p className="section-eyebrow">How it works</p>
          <h2 className="section-title">A calm workflow from discovery to preparation.</h2>
          <p className="body-copy">
            ScholarAI is designed for students who need structure, not noise. Each step
            narrows attention instead of adding another tool to manage.
          </p>
        </article>
        <article className="surface-panel">
          <ol className="flow-list">
            <li>Browse a published catalog with clear filters and visible source boundaries.</li>
            <li>Save a focused profile so recommendations stay explainable and realistic.</li>
            <li>Use writing and interview workspaces that separate facts from coaching.</li>
          </ol>
        </article>
      </section>

      <section className="split-panel">
        <article className="data-callout">
          <p className="list-label">Validated scholarship facts</p>
          <p className="body-copy">
            ScholarAI treats published scholarship records as the authority for scope,
            requirements, funding, and deadlines.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Generated guidance</p>
          <p className="body-copy">
            Explanations and preparation support are layered on top of those records so
            the product stays useful without overstating certainty.
          </p>
        </article>
      </section>

      <section className="route-grid">
        {landingFeatureRoutes.map((route) => (
          <article className="route-card" key={route.href}>
            <StatusBadge
              label={route.section === "discovery" ? "Public workflow" : "Guided workflow"}
              variant={route.section === "discovery" ? "validated" : "generated"}
            />
            <h3 className="route-card__title">{route.label}</h3>
            <p className="route-card__description">{route.description}</p>
            <Link className="nav-link" href={route.href}>
              Open
            </Link>
          </article>
        ))}
      </section>

      <section className="surface-band">
        <div className="button-row">
          <StatusBadge label="MVP posture" variant="neutral" />
          <p className="body-copy">
            Built for a realistic 3-person, 16-week MVP with student trust as the quality bar.
          </p>
        </div>
      </section>
    </MarketingShell>
  );
}
