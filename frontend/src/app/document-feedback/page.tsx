import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function DocumentFeedbackPage() {
  return (
    <AppShell
      title="Document feedback will clearly separate user text, grounded context, and generated guidance."
      description="This placeholder route reserves the bounded RAG workflow without implementing it early."
    >
      <section className="page-grid">
        <article className="surface-card">
          <PageHeader
            title="Validated facts remain separate"
            description="Scholarship-specific constraints will be injected from structured records, not inferred from raw text."
          />
        </article>
        <article className="surface-panel">
          <div className="meta-row">
            <StatusBadge label="Generated guidance" variant="generated" />
            <StatusBadge label="Validated facts" variant="validated" />
          </div>
          <p className="body-copy">
            This UI should later make the difference between scholarship facts
            and writing suggestions visually obvious.
          </p>
        </article>
      </section>
      <section className="split-panel">
        <article className="data-callout">
          <p className="list-label">Later factual inputs</p>
          <p className="body-copy">
            Published requirements, deadlines, and provider constraints.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Later generated outputs</p>
          <p className="body-copy">
            Revision suggestions, missing-point prompts, and tone feedback.
          </p>
        </article>
      </section>
    </AppShell>
  );
}
