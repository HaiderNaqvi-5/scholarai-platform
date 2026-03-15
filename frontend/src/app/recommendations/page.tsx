import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const placeholderItems = [
  {
    title: "Vector Institute Scholarship",
    provider: "University-aligned provider",
    score: "Strong fit",
    note: "Published record only. Explanation will be rule-derived first.",
  },
  {
    title: "Canadian Graduate Funding Award",
    provider: "Canadian university source",
    score: "Possible fit",
    note: "Warnings can show when data is missing or constraints are unclear.",
  },
];

export default function RecommendationsPage() {
  return (
    <AppShell
      title="Recommendations stay narrow, traceable, and grounded in published scholarship records."
      description="The first implementation slice will return a basic list with fit bands, top reasons, and warnings."
    >
      <section className="surface-card">
        <PageHeader
          eyebrow="First slice output"
          title="Recommendation payload shape"
          description="Each item will expose estimated fit, top reasons, and warnings without advanced model claims."
        />
        <div className="placeholder-grid">
          {placeholderItems.map((item) => (
            <article className="placeholder-card" key={item.title}>
              <div className="meta-row">
                <StatusBadge label={item.score} variant="generated" />
                <StatusBadge label="Published source" variant="validated" />
              </div>
              <h3 className="section-title">{item.title}</h3>
              <p className="body-copy">{item.provider}</p>
              <p className="body-copy">{item.note}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="page-grid">
        <article className="data-callout">
          <p className="list-label">Facts shown here</p>
          <p className="body-copy">
            Title, provider, deadline, and published-state hints come from
            structured scholarship records only.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Guidance shown here</p>
          <p className="body-copy">
            Fit bands, top reasons, and warnings are generated from explicit
            eligibility rules in the first slice.
          </p>
        </article>
      </section>
    </AppShell>
  );
}
