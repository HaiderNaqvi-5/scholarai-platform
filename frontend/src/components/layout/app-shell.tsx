"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { AuthActions } from "@/components/auth/auth-actions";
import { Footer } from "@/components/layout/footer";
import { ThemeToggle } from "@/components/theme/theme-toggle";
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
  eyebrow,
  children,
  intro,
}: AppShellProps) {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const visibleRoutes = appNavRoutes.filter(
    (route) => !route.requiresAuth || isAuthenticated,
  );

  return (
    <main className="app-shell" id="main-content">
      <div className="page-shell">
        <nav className="shell-nav shell-nav--app" aria-label="App navigation">
          <Link className="brand-lockup brand-lockup--link" href="/" aria-label="ScholarAI home">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-lockup__text">
              <span className="brand-title">ScholarAI</span>
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
                  aria-current={isActive ? "page" : undefined}
                >
                  {route.label}
                </Link>
              );
            })}
          </div>
          <div className="shell-nav__actions">
            <ThemeToggle />
            <AuthActions />
          </div>
        </nav>
        <header className="hero-block hero-block--app fade-in">
          <div className="hero-block__copy">
            {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
            <h1 className="page-title">{title}</h1>
            <p className="page-description">{description}</p>
          </div>
          {intro ? <div className="shell-intro">{intro}</div> : null}
        </header>
        {children}
      </div>
      <Footer />
    </main>
  );
}
