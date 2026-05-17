import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Badge (Front-upgrade §4.1) — h20, 999 radius, 11px uppercase tracking
 * 0.06em. Reserved for state tags and small status pips. For interactive
 * filter tags, prefer `Chip` (h28).
 */
const badge = cva(
  "inline-flex items-center gap-1 rounded-full px-2 h-5 text-[11px] font-semibold uppercase tracking-[0.06em] leading-none whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral:   "bg-paper-warm text-ink-muted",
        validated: "bg-validated-soft text-validated",
        generated: "bg-generated-soft text-generated",
        caution:   "bg-caution-soft text-caution",
        sindoor:   "bg-sindoor-soft text-sindoor",
        danger:    "bg-sindoor-soft text-sindoor",
        lapis:     "bg-lapis-soft text-lapis",
        gold:      "bg-gold-soft text-gold-leaf",
        ink:       "bg-ink-deep text-paper-white",
        live:      "bg-paper-white text-ink-deep border border-[var(--color-border)]",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badge> {}

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badge({ tone, className }))} {...props} />;
}

/**
 * Chip (Front-upgrade §4.1) — h28, 10 radius, 12px text. Interactive
 * filter / multi-select / cohort tag. Click handler optional.
 */
const chip = cva(
  "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-[10px] text-[12px] font-medium leading-none whitespace-nowrap transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)]",
  {
    variants: {
      tone: {
        neutral:   "bg-paper-warm text-ink-deep hover:bg-paper-edge",
        validated: "bg-validated-soft text-validated",
        generated: "bg-generated-soft text-generated",
        caution:   "bg-caution-soft text-caution",
        sindoor:   "bg-sindoor-soft text-sindoor",
        gold:      "bg-gold-soft text-gold-leaf",
        lapis:     "bg-lapis-soft text-lapis",
        outline:   "bg-paper-white text-ink-deep border border-[var(--color-border)] hover:border-ink-muted/40",
      },
      active: {
        true:  "ring-2 ring-[var(--color-ring)]",
        false: "",
      },
    },
    defaultVariants: { tone: "neutral", active: false },
  },
);

export interface ChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chip> {}

export function Chip({ className, tone, active, ...props }: ChipProps) {
  return <span className={cn(chip({ tone, active, className }))} {...props} />;
}
