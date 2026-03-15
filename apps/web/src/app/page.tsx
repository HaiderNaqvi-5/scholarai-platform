import Link from "next/link";
import { APP_ROUTES } from "@/lib/app-routes";

const routeCards = APP_ROUTES.filter((route) => route.showInLanding);

export default function Home() {
  return (
    <main className="page-frame">
      <section className="hero-panel">
        <div className="space-y-5">
          <p className="eyebrow">ScholarAI MVP frontend scaffold</p>
          <h1 className="hero-title">
            A restrained interface foundation for scholarship discovery and
            preparation.
          </h1>
          <p className="lead max-w-2xl">
            This scaffold establishes the documented route map, shared tokens,
            and editorial UI posture without overbuilding product features. It
            is designed to stay maintainable for a 3-developer MVP.
          </p>
        </div>

        <div className="hero-actions">
          <Link className="primary-link" href="/onboarding">
            Open onboarding scaffold
          </Link>
          <Link className="secondary-link" href="/recommendations">
            Review recommendation route
          </Link>
        </div>
      </section>

      <section className="content-grid">
        {routeCards.map((route) => (
          <article className="tone-card" key={route.href}>
            <div className="space-y-3">
              <p className="token-pill">{route.label}</p>
              <h2 className="section-title">{route.title}</h2>
              <p className="body-copy">{route.summary}</p>
            </div>
            <Link className="inline-link" href={route.href}>
              Open placeholder
            </Link>
          </article>
        ))}
      </section>
    </main>
  );
}
