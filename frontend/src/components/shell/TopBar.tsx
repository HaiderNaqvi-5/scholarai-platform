"use client";

import { Search, LogOut, BellRing } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/ui/icon-button";
import { Badge } from "@/components/ui/badge";
import { hasRole } from "@/lib/auth/RoleGuard";
import { endpoints } from "@/lib/api";
import type { HealthResponse } from "@/lib/api";

/**
 * TopBar (Front-upgrade §3.2) — 60 tall, sticky, paper-white,
 * hairline bottom border. Page title / breadcrumb area on the left
 * (rendered by per-route layouts), search center, avatar menu right.
 *
 * Keyboard: `/` focuses search anywhere on the page (PR-blocking
 * UX constraint per frontend CLAUDE.md).
 */
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
  const initials = user
    ? (user.full_name || user.email)
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "";
  const planLabel = user?.plan
    ? user.plan === "free"
      ? "Explorer"
      : user.plan.replace(/^./, (c) => c.toUpperCase())
    : null;

  return (
    <header className="sticky top-0 z-30 flex h-[60px] items-center gap-3 border-b border-[var(--color-border-quiet)] bg-paper-white/95 px-4 backdrop-blur-md md:px-6">
      <form onSubmit={onSubmit} className="flex flex-1 items-center" role="search">
        <label htmlFor="topbar-search" className="sr-only">
          Search scholarships
        </label>
        <div className="relative w-full max-w-lg">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-subtle"
            strokeWidth={1.5}
            aria-hidden
          />
          <input
            id="topbar-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search scholarships"
            aria-keyshortcuts="/"
            className="h-10 w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white pl-10 pr-12 text-[14px] text-ink-deep placeholder:text-ink-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
          />
          <kbd
            aria-hidden
            className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded border border-[var(--color-border)] bg-paper-warm px-1.5 py-0.5 font-mono text-[10px] text-ink-subtle"
          >
            /
          </kbd>
        </div>
      </form>

      {showAdmin && alertCount > 0 ? (
        <Button
          variant="ghost"
          size="sm"
          aria-label={`${alertCount} health alerts`}
          onClick={() => router.push("/admin")}
        >
          <BellRing className="size-4 text-caution" strokeWidth={1.5} />
          <span className="font-mono tabular-nums text-caution">{alertCount}</span>
        </Button>
      ) : null}

      {user ? (
        <div className="flex items-center gap-3">
          {planLabel ? (
            <Badge tone={user.plan === "elite" ? "gold" : user.plan === "pro" ? "lapis" : "neutral"}>
              {planLabel}
            </Badge>
          ) : null}
          <div className="hidden text-right md:block">
            <p className="text-[13px] font-medium leading-none text-ink-deep">
              {user.full_name || user.email}
            </p>
            <p className="mt-0.5 text-[11px] leading-none text-ink-subtle">
              {user.role.replace(/_/g, " ").toLowerCase()}
            </p>
          </div>
          <span
            className="hidden md:flex size-9 items-center justify-center rounded-full bg-paper-warm font-mono text-[12px] font-semibold text-ink-deep"
            aria-hidden
          >
            {initials || "?"}
          </span>
          <IconButton aria-label="Sign out" onClick={() => auth.logout()}>
            <LogOut className="size-4" strokeWidth={1.5} />
          </IconButton>
        </div>
      ) : null}
    </header>
  );
}
