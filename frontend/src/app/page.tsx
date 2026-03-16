import Link from "next/link";

import { MarketingShell } from "@/components/layout/marketing-shell";

export default function LandingPage() {
  return (
    <MarketingShell
      eyebrow="Scholarship planning"
      title="Find the right scholarships. Know why they fit."
      description="ScholarAI combines a curated Canada-first catalog with profile-aware recommendations and structured preparation tools."
      actions={
        <>
          <Link className="auth-link auth-link--primary" href="/signup">
            Get started
          </Link>
          <Link className="nav-link" href="/scholarships">
            Browse scholarships
          </Link>
        </>
      }
    >
      <section className="landing-hero">
        <div className="hero-trust-rail">
          <article className="data-point">
            <p className="data-point__label">Catalog</p>
            <strong>Canada-first, MS-focused</strong>
            <p className="body-copy">
              Published scholarship records with verified deadlines, requirements, and funding details.
            </p>
          </article>
          <article className="data-point">
            <p className="data-point__label">Trust model</p>
            <strong>Facts lead, guidance follows</strong>
            <p className="body-copy">
              Official scholarship data stays primary. Recommendations and writing help are clearly labeled as advisory.
            </p>
          </article>
          <article className="data-point">
            <p className="data-point__label">Scope</p>
            <strong>Data Science, AI, Analytics</strong>
            <p className="body-copy">
              A focused corpus designed for depth over breadth, with Fulbright-related US coverage included.
            </p>
          </article>
        </div>
      </section>

      <section className="feature-grid" id="how-it-works">
        <article className="surface-card">
          <p className="section-eyebrow">How it works</p>
          <h2 className="section-title">A clear path from discovery to preparation.</h2>
          <p className="body-copy">
            ScholarAI is structured so each step narrows your attention instead of adding more tools to manage.
          </p>
        </article>
        <article className="surface-panel">
          <ol className="flow-list">
            <li>Browse published scholarships with structured filters and visible data boundaries.</li>
            <li>Save a profile so recommendations can explain why each opportunity fits.</li>
            <li>Use writing and interview workspaces that keep coaching separate from official requirements.</li>
          </ol>
        </article>
      </section>

      <section className="split-panel">
        <article className="data-callout">
          <p className="list-label">Verified scholarship data</p>
          <p className="body-copy">
            Requirements, deadlines, and funding come from published records. These are the facts you plan around.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Advisory guidance</p>
          <p className="body-copy">
            Recommendations, writing feedback, and interview practice are layered on top and always labeled as generated.
          </p>
        </article>
      </section>
    </MarketingShell>
  );
}
