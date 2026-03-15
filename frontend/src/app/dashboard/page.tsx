import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function DashboardPage() {
  return (
    <AppShell
      title="The dashboard will remain a calm navigation surface, not a template-heavy control center."
      description="In the foundation phase it exists only to reserve layout structure for later vertical slices."
    >
      <section className="surface-card">
        <PageHeader
          title="Reserved for later integration"
          description="The MVP dashboard should summarize profile readiness, recommendation access, and preparation tools without turning into an analytics-heavy shell."
        />
        <div className="plan-grid">
          <article className="route-card">
            <StatusBadge label="Next slice" variant="planned" />
            <h3 className="route-card__title">Profile readiness</h3>
            <p className="route-card__description">
              Show whether the student has provided the minimum required fields.
            </p>
          </article>
          <article className="route-card">
            <StatusBadge label="Reserved" variant="planned" />
            <h3 className="route-card__title">Recommendation access</h3>
            <p className="route-card__description">
              Link into the recommendation list without adding analytics-heavy widgets.
            </p>
          </article>
        </div>
      </section>
    </AppShell>
  );
}
