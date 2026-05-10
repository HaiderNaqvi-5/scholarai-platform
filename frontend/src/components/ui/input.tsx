"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-subtle",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:border-generated",
        "disabled:cursor-not-allowed disabled:opacity-60",
        "transition-colors duration-150",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
