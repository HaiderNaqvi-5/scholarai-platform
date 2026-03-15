import Link from "next/link";

import { appRoutes } from "@/lib/routes";

type MarketingShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
};

export function MarketingShell({
  eyebrow,
  title,
  description,
  children,
}: MarketingShellProps) {
  return (
    <main className="marketing-shell">
      <div className="page-shell">
        <nav className="top-nav">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true" />
            <p className="brand-title">ScholarAI</p>
          </div>
          <div className="nav-links">
            {appRoutes.slice(1, 5).map((route) => (
              <Link key={route.href} className="nav-link" href={route.href}>
                {route.label}
              </Link>
            ))}
          </div>
        </nav>
        <header className="hero-block">
          <p className="section-eyebrow">{eyebrow}</p>
          <h1 className="hero-title">{title}</h1>
          <p className="page-description">{description}</p>
        </header>
        {children}
      </div>
    </main>
  );
}
