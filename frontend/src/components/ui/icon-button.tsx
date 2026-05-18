"use client";

import { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * IconButton (Front-upgrade §4.1) — square 44×44, transparent → paper-warm
 * hover, ink-muted icon → ink-deep on hover. Carries aria-label.
 */
const iconButton = cva(
  "inline-flex items-center justify-center rounded-[10px] will-change-transform transition-[background-color,color,transform] duration-[var(--motion-micro)] ease-[var(--ease-out)] active:scale-[0.96] active:duration-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-ivory)] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100",
  {
    variants: {
      tone: {
        ghost:  "text-ink-muted hover:bg-paper-warm hover:text-ink-deep",
        solid:  "bg-ink-deep text-paper-white hover:bg-ink",
        danger: "text-sindoor hover:bg-sindoor-soft",
      },
      size: {
        sm: "size-9",
        md: "size-11",
        lg: "size-13",
      },
    },
    defaultVariants: { tone: "ghost", size: "md" },
  },
);

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButton> {
  /** Required for a11y — icon buttons must announce their purpose. */
  "aria-label": string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, tone, size, type = "button", children, ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(iconButton({ tone, size, className }))}
      {...props}
    >
      {children}
    </button>
  ),
);
IconButton.displayName = "IconButton";
