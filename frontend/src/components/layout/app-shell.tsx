"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { AuthActions } from "@/components/auth/auth-actions";
import { appNavRoutes } from "@/lib/routes";

type AppShellProps = {
  title: string;
  description: string;
  eyebrow?: string;
  children: React.ReactNode;
  intro?: React.ReactNode;
};

export function AppShell({
  title,
  description,
  eyebrow = "ScholarAI workspace",
  children,
  intro,
}: AppShellProps) {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const visibleRoutes = appNavRoutes.filter(
    (route) => !route.requiresAuth || isAuthenticated,
  );

  return (
    <main className="app-shell">
      <div className="page-shell">
        <nav className="shell-nav shell-nav--app">
          <Link className="brand-lockup brand-lockup--link" href="/">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-lockup__text">
              <span className="brand-title">ScholarAI</span>
              <span className="brand-subtitle">Calm, structured scholarship planning</span>
            </span>
          </Link>
          <div className="shell-nav__links">
            {visibleRoutes.map((route) => {
              const isActive =
                pathname === route.href || pathname.startsWith(`${route.href}/`);

              return (
                <Link
                  key={route.href}
                  className={isActive ? "shell-nav__link shell-nav__link--active" : "shell-nav__link"}
                  href={route.href}
                >
                  {route.label}
                </Link>
              );
            })}
          </div>
          <AuthActions />
        </nav>
        <header className="hero-block hero-block--app">
          <div className="hero-block__copy">
            <p className="section-eyebrow">{eyebrow}</p>
            <h1 className="page-title">{title}</h1>
            <p className="page-description">{description}</p>
          </div>
          {intro ? <div className="shell-intro">{intro}</div> : null}
        </header>
        {children}
      </div>
    </main>
  );
}
