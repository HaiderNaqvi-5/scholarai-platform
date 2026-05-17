"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Bookmark,
  FileText,
  Mic,
  User,
  Settings,
  LayoutDashboard,
  ClipboardCheck,
  Database,
  Users,
  ScrollText,
  GaugeCircle,
  KanbanSquare,
  ListChecks,
  Plane,
  Sparkles,
  Building2,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/AuthProvider";
import { hasRole } from "@/lib/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  shortcut?: string;
};

type Section = {
  title: string;
  items: NavItem[];
  showFor: "student" | "mentor" | "admin" | "partner";
};

/**
 * Sidebar nav (Front-upgrade §3.2 + §3.3).
 * Student order: Dashboard, Matches, Tracker, Documents, Interviews,
 * Discover, Saved, Profile, Settings. Footer cluster carries
 * TrialBanner + DemoBanner + Upgrade button.
 */
const sections: Section[] = [
  {
    title: "Apply",
    showFor: "student",
    items: [
      { href: "/feed", label: "Dashboard", icon: LayoutDashboard, shortcut: "G F" },
      { href: "/dashboard/scholarships/match", label: "Matches", icon: Sparkles, shortcut: "G M" },
      { href: "/tracker", label: "Tracker", icon: KanbanSquare, shortcut: "G T" },
      { href: "/discover", label: "Discover", icon: Compass, shortcut: "G D" },
      { href: "/saved", label: "Saved", icon: Bookmark, shortcut: "G S" },
    ],
  },
  {
    title: "Prepare",
    showFor: "student",
    items: [
      { href: "/documents", label: "Documents", icon: FileText },
      { href: "/interviews", label: "Interviews", icon: Mic },
      { href: "/interviews/visa", label: "Visa practice", icon: Plane },
    ],
  },
  {
    title: "Account",
    showFor: "student",
    items: [
      { href: "/profile", label: "Profile", icon: User },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
  {
    title: "Mentor",
    showFor: "mentor",
    items: [{ href: "/mentor/queue", label: "Review queue", icon: ClipboardCheck }],
  },
  {
    title: "Partners",
    showFor: "partner",
    items: [
      { href: "/partners", label: "Overview", icon: Building2 },
      { href: "/partners/universities", label: "Universities", icon: GaugeCircle },
    ],
  },
  {
    title: "Admin",
    showFor: "admin",
    items: [
      { href: "/admin", label: "Overview", icon: GaugeCircle },
      { href: "/admin/ingestion", label: "Ingestion", icon: Database },
      { href: "/admin/curation", label: "Curation", icon: ListChecks },
      { href: "/admin/rec-eval", label: "Rec eval", icon: ListChecks },
      { href: "/admin/users", label: "Users", icon: Users },
      { href: "/admin/audit", label: "Audit", icon: ScrollText },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const auth = useAuth();
  const user = auth.status === "authed" ? auth.user : null;

  const plan = user?.plan ?? null;
  const expiry = user?.plan_expires_at ?? null;
  const showTrial = plan === "pro" && Boolean(expiry);

  /* `Date.now()` is impure; compute trial countdown only after hydration. */
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  useEffect(() => {
    if (!showTrial || !expiry) return;
    const tick = () => {
      const ms = new Date(expiry).getTime() - Date.now();
      setTrialDaysLeft(Math.max(0, Math.ceil(ms / 86_400_000)));
    };
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, [showTrial, expiry]);

  const isFree = plan === "free" || !plan;

  return (
    <aside
      className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-[var(--color-border-quiet)] md:bg-paper-white"
      aria-label="Primary navigation"
    >
      {/* Brand mark */}
      <div className="flex h-[60px] items-center px-5 border-b border-[var(--color-border-quiet)]">
        <Link
          href={user ? "/feed" : "/"}
          className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
        >
          {BRAND_DISPLAY_NAME}
        </Link>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4" aria-label="Sections">
        {sections
          .filter((s) => hasRole(user, s.showFor))
          .map((section) => (
            <div key={section.title}>
              <p className="mb-1.5 px-3 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-subtle">
                {section.title}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => {
                  const active =
                    pathname === item.href ||
                    (item.href !== "/feed" && pathname.startsWith(item.href + "/"));
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        prefetch
                        className={cn(
                          "group flex items-center gap-3 rounded-[10px] px-3 py-2 text-[14px] transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)] tap-target",
                          active
                            ? "bg-lapis-soft text-lapis font-medium"
                            : "text-ink-muted hover:bg-paper-warm hover:text-ink-deep",
                        )}
                        aria-current={active ? "page" : undefined}
                      >
                        <Icon
                          className={cn("size-[18px] shrink-0", active && "text-lapis")}
                          strokeWidth={1.5}
                        />
                        <span className="flex-1">{item.label}</span>
                        {item.shortcut ? (
                          <kbd className="hidden font-mono text-[10px] text-ink-subtle group-hover:inline">
                            {item.shortcut}
                          </kbd>
                        ) : null}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
      </nav>

      {/* Footer cluster: TrialBanner / DemoBanner / Upgrade button */}
      {user ? (
        <div className="flex flex-col gap-2 border-t border-[var(--color-border-quiet)] p-3">
          {showTrial && trialDaysLeft !== null ? (
            <div
              className={cn(
                "rounded-[12px] px-3 py-2",
                trialDaysLeft <= 7
                  ? "bg-gold-soft border border-gold-leaf/30"
                  : "bg-paper-warm border border-[var(--color-border-quiet)]",
              )}
            >
              <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-gold-leaf">
                Pro trial
              </p>
              <p className="mt-0.5 font-mono text-[13px] tabular-nums text-ink-deep">
                {trialDaysLeft} day{trialDaysLeft === 1 ? "" : "s"} left
              </p>
            </div>
          ) : null}
          {isFree ? (
            <Button asChild variant="gold" size="sm" className="w-full">
              <Link href="/upgrade">See Pro</Link>
            </Button>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
