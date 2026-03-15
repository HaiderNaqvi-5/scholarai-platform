"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_ROUTES } from "@/lib/app-routes";

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="header-frame">
        <Link className="brand-mark" href="/">
          <span className="brand-name">ScholarAI</span>
          <span className="brand-meta">MVP frontend scaffold</span>
        </Link>

        <nav aria-label="Primary" className="nav-row">
          {APP_ROUTES.filter((route) => route.showInNav).map((route) => {
            const isActive = pathname === route.href;

            return (
              <Link
                key={route.href}
                className={`nav-link${isActive ? " nav-link-active" : ""}`}
                href={route.href}
              >
                {route.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
