import { forwardRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Card primitives — 18px radius (Front-upgrade §2.3), 20 padding,
 * hairline border + opt-in lift shadow on clickable cards.
 *
 * Composition:
 *   <Card hoverable> | <Card asPanel> for 22 radius + 24 padding
 *     <CardHeader> ... <CardTitle> + optional eyebrow ... </CardHeader>
 *     <CardBody>   ... </CardBody>
 *     <CardFooter> ... </CardFooter>
 *   </Card>
 *
 * Stripes (validated / generated / caution / danger) compose via the
 * `*-stripe` utilities defined in globals.css — never combine two.
 */

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Adds lift shadow + ink-muted border on hover. Use only on clickable cards. */
  hoverable?: boolean;
  /** Upgrades radius (22) + base padding (24) for organism panels. */
  asPanel?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverable, asPanel, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        asPanel
          ? "rounded-[22px] p-6"
          : "rounded-[18px]",
        "border border-[var(--color-border)] bg-paper-white",
        "transition-[box-shadow,border-color] duration-[var(--motion-micro)] ease-[var(--ease-out)]",
        hoverable &&
          "cursor-pointer hover:shadow-[var(--shadow-lift)] hover:border-ink-muted/30",
        className,
      )}
      {...props}
    />
  ),
);
Card.displayName = "Card";

export const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-1.5 p-5 pb-3", className)} {...props} />
);

export const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3
    className={cn(
      "text-[17px] font-semibold leading-[1.4] tracking-[-0.005em] text-ink-deep",
      "font-sans", /* card titles use Inter 17/600, not Fraunces — §2.2 */
      className,
    )}
    {...props}
  />
);

export const CardDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn("text-sm text-ink-muted", className)} {...props} />
);

/** Optional small eyebrow above CardTitle — microlabels +0.06em tracking per §2.2 */
export const CardEyebrow = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p
    className={cn(
      "font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle",
      className,
    )}
    {...props}
  />
);

export const CardBody = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-5 pt-2", className)} {...props} />
);

export const CardFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex items-center gap-2 p-5 pt-3", className)} {...props} />
);
