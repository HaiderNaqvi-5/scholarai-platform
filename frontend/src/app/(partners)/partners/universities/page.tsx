/**
 * /partners/universities — university partner directory (stub).
 *
 * Stub for FYP. Backend `POST /api/v1/b2b/share` is wired and gated by
 * institution-tier + dpa_signed_at + b2b_share_consent. UI for browsing
 * snapshots and rejecting shares is post-FYP.
 */

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/section-header";
import { partnershipsMailto, PARTNERSHIPS_EMAIL } from "@/lib/brand";

export default function PartnerUniversitiesPage() {
  return (
    <div data-testid="partners-universities" className="space-y-6">
      <PageHeader
        title="Universities"
        description="Foreign universities receiving Pakistani applicant snapshots via your DPA-signed partner account."
      />

      <Card>
        <CardHeader>
          <CardTitle>No shared profiles yet</CardTitle>
        </CardHeader>
        <CardBody className="text-sm text-ink-muted">
          <p>
            Students must opt in to B2B sharing before their profile reaches your
            dashboard. Send your registrar&apos;s email to{" "}
            <a href={partnershipsMailto()} className="underline">
              {PARTNERSHIPS_EMAIL}
            </a>{" "}
            so we can confirm the DPA is countersigned for your institution.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
