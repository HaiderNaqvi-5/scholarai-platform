"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export function OwnerDashboardShell() {
  return (
    <AppShell
      eyebrow="Owner Home"
      title="Platform oversight and governance controls."
      description="Review system-level governance posture and navigate to owner-scoped controls."
    >
      <section className="metrics-grid" data-testid="owner-dashboard-shell">
        <article className="data-point">
          <p className="data-point__label">Stage conformance</p>
          <strong>v0.1 internal</strong>
          <p className="body-copy">Governance checks are available through admin analytics and audit surfaces.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Policy scope</p>
          <strong>Owner controls active</strong>
          <p className="body-copy">Owner role includes system-read oversight with elevated governance visibility.</p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Governance"
            title="Platform governance pathways"
            description="Owner home centralizes stage conformance and policy oversight entry points."
          />
          <div className="surface-list">
            <article>
              <p className="list-heading">Admin analytics visibility</p>
              <p className="body-copy">
                Access aggregated operational metrics, ingestion health, and KPI trend snapshots from the Admin surface.
              </p>
            </article>
            <article>
              <p className="list-heading">Role and capability governance</p>
              <p className="body-copy">
                Monitor role-capability posture and ensure owner-only controls remain scoped to governance workflows.
              </p>
            </article>
          </div>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Trust boundary"
            title="Operational framing"
            description="Owner oversight tracks conformance and policy; user-facing scholarship facts remain sourced from published data."
          />
          <div className="meta-row">
            <StatusBadge label="Owner system read" variant="validated" />
            <StatusBadge label="Governance oversight" variant="generated" />
          </div>
        </article>
      </section>
    </AppShell>
  );
}
