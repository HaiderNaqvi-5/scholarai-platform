"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Input — 44h, 10 radius, 15px text. Focus shows 2px lapis ring (no
 * border color change per §2.3). Placeholder uses ink-subtle for low
 * contrast that still passes 4.5:1.
 */
export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-11 w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3.5 py-2",
        "text-[15px] text-ink-deep placeholder:text-ink-subtle",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-0",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-paper-warm",
        "transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)]",
        "tap-target",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

/**
 * Textarea — same chrome as Input, auto-grow 4–16 rows via rows prop.
 */
export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, rows = 4, ...props }, ref) => (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(
        "flex w-full rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3.5 py-3",
        "text-[15px] text-ink-deep placeholder:text-ink-subtle leading-[1.55]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-paper-warm",
        "transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)] resize-y",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";
