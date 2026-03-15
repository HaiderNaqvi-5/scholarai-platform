import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function ProfilePage() {
  return (
    <AppShell
      title="Profile data becomes the input contract for the first recommendation slice."
      description="This page will later persist the canonical student profile that drives eligibility filtering."
    >
      <section className="page-grid">
        <article className="surface-card">
          <PageHeader
            title="Student profile contract"
            description="The first persisted profile will remain narrow and schema-aligned with the backend."
          />
          <p className="code-note">
            PUT /api/v1/profile
            <br />
            GET /api/v1/profile
          </p>
        </article>
        <article className="surface-panel">
          <div className="meta-row">
            <StatusBadge label="Rules-first slice" variant="generated" />
            <StatusBadge label="No broad profile wizard" variant="planned" />
          </div>
          <p className="body-copy">
            The frontend flow after this phase will move from profile capture
            directly into a recommendation request without introducing advanced
            planning or document features prematurely.
          </p>
        </article>
      </section>
      <section className="surface-card">
        <PageHeader
          eyebrow="Bounded contract"
          title="Backend-aligned fields"
          description="The frontend contract stays intentionally close to the API schema to avoid early translation layers."
        />
        <div className="surface-list">
          <article>
            <p className="list-heading">Identity and eligibility</p>
            <p className="body-copy">
              citizenship_country_code, target_country_code, target_degree_level
            </p>
          </article>
          <article>
            <p className="list-heading">Academic fit</p>
            <p className="body-copy">
              target_field, gpa_value, gpa_scale
            </p>
          </article>
          <article>
            <p className="list-heading">Language evidence</p>
            <p className="body-copy">
              language_test_type, language_test_score
            </p>
          </article>
        </div>
      </section>
    </AppShell>
  );
}
