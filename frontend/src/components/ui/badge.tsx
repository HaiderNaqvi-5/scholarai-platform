import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badge = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium leading-none whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-paper-warm text-ink-muted",
        validated: "bg-validated-soft text-validated",
        generated: "bg-generated-soft text-generated",
        caution: "bg-caution-soft text-caution",
        danger: "bg-danger-soft text-danger",
        ink: "bg-ink text-paper",
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
