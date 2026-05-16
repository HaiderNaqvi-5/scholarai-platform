/**
 * /partners/universities — university partner directory (stub).
 *
 * Stub for FYP. Backend `POST /api/v1/b2b/share` is wired and gated by
 * institution-tier + dpa_signed_at + b2b_share_consent. UI for browsing
 * snapshots and rejecting shares is post-FYP.
 */

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { partnershipsMailto, PARTNERSHIPS_EMAIL } from "@/lib/brand";

export default function PartnerUniversitiesPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Universities</h1>
        <p className="mt-1 text-ink-muted">
          Foreign universities receiving Pakistani applicant snapshots via your
          DPA-signed partner account.
        </p>
      </header>

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
