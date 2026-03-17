import Link from "next/link";

import { MarketingShell } from "@/components/layout/marketing-shell";

export default function NotFound() {
  return (
    <MarketingShell
      eyebrow="Page not found"
      title="This page doesn't exist."
      description="The URL may have changed, or the page may have been removed. Try going back to the homepage."
      actions={
        <>
          <Link className="auth-link auth-link--primary" href="/">
            Back to home
          </Link>
          <Link className="nav-link" href="/scholarships">
            Browse scholarships
          </Link>
        </>
      }
    >
      <section className="surface-card">
        <p className="section-eyebrow">404</p>
        <h2 className="section-title">
          If you were looking for a scholarship, try the catalog instead.
        </h2>
        <p className="body-copy">
          Published scholarships are always accessible from the main navigation. 
          If you followed a link that led here, the record may have been unpublished or moved.
        </p>
      </section>
    </MarketingShell>
  );
}
