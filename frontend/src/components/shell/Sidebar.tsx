"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Bookmark,
  FileText,
  Mic,
  User,
  Settings,
  Home,
  ClipboardCheck,
  Database,
  Users,
  ScrollText,
  GaugeCircle,
  KanbanSquare,
  ListChecks,
  Plane,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/AuthProvider";
import { hasRole } from "@/lib/auth/RoleGuard";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  shortcut?: string;
};

type Section = {
  title: string;
  items: NavItem[];
  showFor: "student" | "mentor" | "admin";
};

const sections: Section[] = [
  {
    title: "Apply",
    showFor: "student",
    items: [
      { href: "/feed", label: "For you", icon: Home, shortcut: "G F" },
      { href: "/discover", label: "Discover", icon: Compass, shortcut: "G D" },
      { href: "/saved", label: "Saved", icon: Bookmark, shortcut: "G S" },
      { href: "/tracker", label: "Tracker", icon: KanbanSquare, shortcut: "G T" },
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

  return (
    <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-[var(--color-border)] md:bg-paper">
      <div className="flex h-16 items-center px-5">
        <Link href="/feed" className="font-display text-lg tracking-tight text-ink">
          GrantPath
        </Link>
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 pb-6" aria-label="Primary">
        {sections
          .filter((s) => hasRole(user, s.showFor))
          .map((section) => (
            <div key={section.title}>
              <p className="mb-1 px-3 text-[11px] font-medium uppercase tracking-[0.08em] text-ink-subtle">
                {section.title}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => {
                  const active =
                    pathname === item.href || pathname.startsWith(item.href + "/");
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        prefetch
                        className={cn(
                          "group flex items-center gap-3 rounded-[12px] px-3 py-2 text-sm transition-colors duration-150",
                          active
                            ? "bg-paper-warm text-ink"
                            : "text-ink-muted hover:bg-paper-warm hover:text-ink",
                        )}
                      >
                        <Icon className="size-[18px] shrink-0" strokeWidth={1.75} />
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
    </aside>
  );
}
