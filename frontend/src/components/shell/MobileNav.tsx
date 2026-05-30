"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/AuthProvider";
import { primaryGroup } from "@/lib/auth/RoleGuard";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";
import { sections } from "./Sidebar";

/**
 * Mobile navigation drawer (<768px). The Sidebar is `hidden md:flex`, so
 * below the md breakpoint authed users have no nav surface. This hamburger
 * lives in the TopBar and opens a left-anchored Radix drawer rendering the
 * same role-filtered `sections` list. Closes on link tap, Esc, or scrim.
 */
export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const auth = useAuth();
  const user = auth.status === "authed" ? auth.user : null;
  const visible = user ? sections.filter((s) => s.showFor === primaryGroup(user.role)) : [];

  return (
    <DialogPrimitive.Root open={open} onOpenChange={setOpen}>
      <DialogPrimitive.Trigger asChild>
        <button
          type="button"
          aria-label="Open navigation"
          className="md:hidden inline-flex tap-target items-center justify-center rounded-[10px] text-ink-muted transition-colors hover:bg-paper-warm hover:text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
        >
          <Menu className="size-5" strokeWidth={1.5} />
        </button>
      </DialogPrimitive.Trigger>

      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-ink/40 transition-opacity duration-[var(--motion-enter)] ease-[var(--ease-out)] data-[state=closed]:opacity-0 data-[state=open]:opacity-100 data-[state=closed]:duration-[var(--motion-exit)] md:hidden" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="fixed inset-y-0 left-0 z-50 flex w-[80%] max-w-[300px] flex-col bg-paper-white shadow-lg will-change-transform transition-transform duration-[var(--motion-enter)] ease-[var(--ease-out)] data-[state=closed]:-translate-x-full data-[state=open]:translate-x-0 data-[state=closed]:duration-[var(--motion-exit)] focus-visible:outline-none md:hidden"
        >
          <div className="flex h-[60px] items-center justify-between border-b border-[var(--color-border-quiet)] px-5">
            <DialogPrimitive.Title asChild>
              <Link
                href={user ? "/feed" : "/"}
                onClick={() => setOpen(false)}
                className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
              >
                {BRAND_DISPLAY_NAME}
              </Link>
            </DialogPrimitive.Title>
            <DialogPrimitive.Close
              aria-label="Close navigation"
              className="inline-flex tap-target items-center justify-center rounded-[10px] text-ink-subtle transition-colors hover:bg-paper-warm hover:text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
            >
              <X className="size-5" strokeWidth={1.5} />
            </DialogPrimitive.Close>
          </div>

          <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4" aria-label="Sections">
            {visible.map((section) => (
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
                          onClick={() => setOpen(false)}
                          aria-current={active ? "page" : undefined}
                          className={cn(
                            "flex items-center gap-3 rounded-[10px] px-3 py-2 text-[14px] tap-target transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)]",
                            active
                              ? "bg-lapis-soft text-lapis font-medium"
                              : "text-ink-muted hover:bg-paper-warm hover:text-ink-deep",
                          )}
                        >
                          <Icon
                            className={cn("size-[18px] shrink-0", active && "text-lapis")}
                            strokeWidth={1.5}
                          />
                          <span>{item.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
