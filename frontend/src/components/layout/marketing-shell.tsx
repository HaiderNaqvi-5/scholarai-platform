"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { AuthActions } from "@/components/auth/auth-actions";
import { marketingNavLinks } from "@/lib/routes";

type MarketingShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

export function MarketingShell({
  eyebrow,
  title,
  description,
  children,
  actions,
}: MarketingShellProps) {
  const pathname = usePathname();

  return (
    <main className="marketing-shell">
      <div className="page-shell page-shell--marketing">
        <nav className="shell-nav shell-nav--marketing">
          <Link className="brand-lockup brand-lockup--link" href="/">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-lockup__text">
              <span className="brand-title">ScholarAI</span>
            </span>
          </Link>
          <div className="shell-nav__links">
            {marketingNavLinks.map((link) => (
              <Link
                key={link.href}
                className={
                  pathname === link.href || pathname.startsWith("/scholarships")
                    ? "shell-nav__link shell-nav__link--active"
                    : "shell-nav__link"
                }
                href={link.href}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <AuthActions />
        </nav>
        <header className="hero-block hero-block--marketing">
          <div className="hero-block__copy">
            <p className="section-eyebrow">{eyebrow}</p>
            <h1 className="hero-title">{title}</h1>
            <p className="page-description">{description}</p>
          </div>
          {actions ? <div className="hero-actions">{actions}</div> : null}
        </header>
        {children}
      </div>
    </main>
  );
}
