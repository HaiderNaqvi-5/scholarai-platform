"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Button — Premium Cultural variants (Front-upgrade §4.1).
 *
 * - `primary`   ink-deep bg, paper-white text. Default CTA.
 * - `lapis`     lapis bg, paper-white text. Use for premium / link actions
 *               where the surface already carries an ink-deep element.
 * - `secondary` paper-white bg, ink-deep text, 1px hairline border.
 * - `ghost`     transparent, ink-muted text, paper-warm hover.
 * - `danger`    sindoor bg. Destructive.
 * - `gold`      gold-leaf bg. Trial / Pro upgrade CTAs only.
 * - `validated` validated bg. Confirm / approve.
 *
 * Sizes follow §4.1 scale: sm 36 / md 44 / lg 52. Min hit 44×44 always
 * (the sm row uses the tap-target utility to inflate hit area only).
 */
const button = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[12px] font-medium leading-none will-change-transform transition-[background-color,color,border-color,transform,box-shadow,opacity] duration-[var(--motion-micro)] ease-[var(--ease-out)] active:scale-[0.97] active:duration-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-ivory)] disabled:pointer-events-none disabled:opacity-50 disabled:active:scale-100",
  {
    variants: {
      variant: {
        primary:
          "bg-ink-deep text-paper-white shadow-[var(--shadow-hairline)] hover:bg-ink active:bg-[#000]",
        lapis:
          "bg-lapis text-paper-white shadow-[var(--shadow-hairline)] hover:opacity-90 active:opacity-100",
        secondary:
          "bg-paper-white text-ink-deep border border-[var(--color-border)] hover:bg-paper-warm hover:border-ink-muted/40",
        ghost:
          "bg-transparent text-ink-muted hover:bg-paper-warm hover:text-ink-deep",
        danger:
          "bg-sindoor text-paper-white shadow-[var(--shadow-hairline)] hover:opacity-90",
        gold:
          "bg-gold-leaf text-paper-white shadow-[var(--shadow-hairline)] hover:opacity-90",
        validated:
          "bg-validated text-paper-white shadow-[var(--shadow-hairline)] hover:opacity-90",
        link:
          "bg-transparent text-lapis underline underline-offset-4 decoration-1 hover:decoration-2 px-0",
      },
      size: {
        sm: "h-9 px-3 text-[13px] tap-target",
        md: "h-11 px-4 text-[14px]",
        lg: "h-13 px-6 text-[15px]",
        icon: "size-11",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, loading, disabled, children, ...props }, ref) => {
    if (asChild) {
      return (
        <Slot
          ref={ref}
          className={cn(button({ variant, size, className }))}
          {...props}
        >
          {children}
        </Slot>
      );
    }
    return (
      <button
        ref={ref}
        className={cn(button({ variant, size, className }))}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading ? (
          <span
            className="size-[18px] animate-spin [animation-duration:700ms] rounded-full border-2 border-current border-t-transparent"
            aria-hidden
          />
        ) : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
