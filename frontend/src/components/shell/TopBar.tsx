"use client";

import { Search, LogOut, BellRing } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { hasRole } from "@/lib/auth/RoleGuard";
import { endpoints } from "@/lib/api";
import type { HealthResponse } from "@/lib/api";

export function TopBar() {
  const auth = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const user = auth.status === "authed" ? auth.user : null;
  const showAdmin = hasRole(user, "admin");

  useEffect(() => {
    if (!showAdmin) return;
    let cancelled = false;
    const tick = () =>
      endpoints.analytics
        .health()
        .then((h) => {
          if (!cancelled) setHealth(h);
        })
        .catch(() => undefined);
    tick();
    const id = setInterval(tick, 60_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [showAdmin]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "/" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        document.getElementById("topbar-search")?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    router.push(`/discover?query=${encodeURIComponent(q)}`);
  };

  const alertCount = health?.kpi_alerts?.length ?? 0;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-[var(--color-border)] bg-paper/80 px-4 backdrop-blur md:px-6">
      <form onSubmit={onSubmit} className="flex flex-1 items-center" role="search">
        <label htmlFor="topbar-search" className="sr-only">
          Search scholarships
        </label>
        <div className="relative w-full max-w-lg">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-subtle"
            strokeWidth={1.75}
            aria-hidden
          />
          <input
            id="topbar-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search scholarships  (press / to focus)"
            className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white pl-10 pr-3 text-[15px] text-ink placeholder:text-ink-subtle focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
          />
        </div>
      </form>

      {showAdmin && alertCount > 0 ? (
        <Button
          variant="ghost"
          size="sm"
          aria-label={`${alertCount} health alerts`}
          onClick={() => router.push("/admin")}
        >
          <BellRing className="size-4 text-caution" strokeWidth={1.75} />
          <span className="text-caution">{alertCount}</span>
        </Button>
      ) : null}

      {user ? (
        <div className="flex items-center gap-3">
          <div className="hidden text-right md:block">
            <p className="text-sm font-medium text-ink leading-none">{user.full_name || user.email}</p>
            <p className="mt-0.5 text-xs text-ink-subtle leading-none">{user.role.replace(/_/g, " ").toLowerCase()}</p>
          </div>
          <Button variant="ghost" size="icon" aria-label="Sign out" onClick={() => auth.logout()}>
            <LogOut className="size-4" strokeWidth={1.75} />
          </Button>
        </div>
      ) : null}
    </header>
  );
}
