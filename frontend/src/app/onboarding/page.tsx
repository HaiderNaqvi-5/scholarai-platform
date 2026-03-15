import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function OnboardingPage() {
  return (
    <ProtectedRoute>
      <AppShell
        title="Onboarding keeps the first profile pass tight and intentional."
        description="This route will later collect only the fields needed to power the first recommendation slice."
      >
        <section className="page-grid">
          <article className="surface-card">
            <PageHeader
              eyebrow="Step 1"
              title="What the first form will collect"
              description="Citizenship, GPA, target field, degree level, target country, and language score."
            />
            <ul className="field-list">
              <li>Citizenship country</li>
              <li>GPA value and GPA scale</li>
              <li>Target field and degree level</li>
              <li>Target country</li>
              <li>Language test type and score</li>
            </ul>
          </article>
          <article className="surface-panel">
            <div className="meta-row">
              <StatusBadge label="Validated fields first" variant="validated" />
              <StatusBadge label="No AI yet" variant="planned" />
            </div>
            <p className="body-copy">
              This foundation phase avoids a long intake flow. The first usable
              profile only captures the inputs needed for rule-based eligibility
              and a basic recommendation list.
            </p>
          </article>
        </section>
        <section className="surface-card">
          <PageHeader
            eyebrow="Vertical slice"
            title="Profile to recommendations flow"
            description="This page stays deliberately narrow so the next implementation step can ship one end-to-end path without dragging in deferred product areas."
          />
          <ol className="flow-list">
            <li>User confirms a small set of profile facts.</li>
            <li>The frontend writes the canonical profile contract.</li>
            <li>The recommendations view requests published scholarships only.</li>
            <li>The UI renders fit bands, reasons, and warnings.</li>
          </ol>
        </section>
      </AppShell>
    </ProtectedRoute>
  );
}
