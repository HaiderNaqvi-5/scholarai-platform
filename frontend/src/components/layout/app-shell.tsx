import Link from "next/link";

import { appRoutes } from "@/lib/routes";

type AppShellProps = {
  title: string;
  description: string;
  eyebrow?: string;
  children: React.ReactNode;
};

export function AppShell({
  title,
  description,
  eyebrow = "Implementation foundation",
  children,
}: AppShellProps) {
  return (
    <main className="app-shell">
      <div className="page-shell">
        <nav className="top-nav">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true" />
            <p className="brand-title">ScholarAI</p>
          </div>
          <div className="nav-links">
            {appRoutes.map((route) => (
              <Link key={route.href} className="nav-link" href={route.href}>
                {route.label}
              </Link>
            ))}
          </div>
        </nav>
        <header className="page-header">
          <p className="section-eyebrow">{eyebrow}</p>
          <h1 className="page-title">{title}</h1>
          <p className="page-description">{description}</p>
        </header>
        <div className="mode-banner">
          <span className="mode-banner__label">Foundation phase</span>
          <p className="mode-banner__copy">
            Structured validated data remains the authority. Placeholder pages
            reserve workflows without implying shipped functionality.
          </p>
        </div>
        {children}
      </div>
    </main>
  );
}
