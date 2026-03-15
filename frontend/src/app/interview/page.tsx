import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function InterviewPage() {
  return (
    <ProtectedRoute>
      <AppShell
        title="Interview practice starts as a text-first, rubric-based workflow."
        description="Audio-first interaction stays deferred until the core recommendation and profile slice is stable."
      >
        <section className="page-grid">
          <article className="surface-card">
            <PageHeader
              title="Initial MVP posture"
              description="Generate bounded scholarship-style prompts and return structured rubric feedback."
            />
          </article>
          <article className="surface-panel">
            <div className="meta-row">
              <StatusBadge label="Text first" variant="planned" />
              <StatusBadge label="Audio deferred" variant="warning" />
            </div>
            <p className="body-copy">
              The first coding phase only reserves the route and layout. It does
              not implement transcription or advanced interview simulation.
            </p>
          </article>
        </section>
        <section className="surface-card">
          <PageHeader
            eyebrow="Scoring posture"
            title="Structured rubric, not conversational sprawl"
            description="When this workflow is implemented, feedback should stay sectioned into clarity, relevance, evidence, and improvement prompts."
          />
          <div className="number-grid">
            <article>
              <strong>Prompt</strong>
              <p className="body-copy">Scholarship-style question with bounded context.</p>
            </article>
            <article>
              <strong>Response</strong>
              <p className="body-copy">Student answer in text, with voice deferred.</p>
            </article>
            <article>
              <strong>Rubric feedback</strong>
              <p className="body-copy">Structured scores and actionable next improvements.</p>
            </article>
          </div>
        </section>
      </AppShell>
    </ProtectedRoute>
  );
}
