/**
 * /partners — institution admin home (PRD §0.6).
 *
 * Stub for FYP: the B2B endpoint `POST /api/v1/b2b/share` is live, so an
 * institution admin can see which students have opted in. Outcome dashboards
 * and referral invoicing are post-FYP.
 */

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/section-header";

export default function PartnersHome() {
  return (
    <div data-testid="partners-overview" className="space-y-6">
      <PageHeader
        eyebrow="Institution"
        title="Partner overview"
        description="Visibility into AidwiseAI applicants who have opted in to share their profile with your institution. Trust boundary: this surface is fully isolated from the student recommendation engine."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Shared profiles</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="font-mono text-[28px] font-semibold tabular-nums text-ink-deep">—</p>
            <p className="mt-1 text-sm text-ink-muted">
              Students who opted in to B2B sharing with your DPA-signed
              institution.
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Pending consent</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="font-mono text-[28px] font-semibold tabular-nums text-ink-deep">—</p>
            <p className="mt-1 text-sm text-ink-muted">
              Matches who have not yet granted B2B share consent.
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Enrolments</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="font-mono text-[28px] font-semibold tabular-nums text-ink-deep">—</p>
            <p className="mt-1 text-sm text-ink-muted">
              Referral enrolments confirmed by your registrar (post-FYP).
            </p>
          </CardBody>
        </Card>
      </div>

      <Card className="bg-paper-warm/40">
        <CardBody className="text-sm text-ink-muted">
          <p>
            <strong className="text-ink">Roadmap.</strong> Bulk roster import,
            aggregate outcome dashboards, and the referral-fee invoicing flow
            are scheduled for the post-FYP B2B sprint.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
