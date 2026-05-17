import { cn } from "@/lib/utils";

/**
 * Skeleton — paper-edge fill, opacity-only pulse (1.2s, 0.6→1).
 * No shimmer animation (banned theatre per Front-upgrade §1.3).
 *
 * `block`  default — rectangular placeholder for cards / panels
 * `text`   inline text line (h ≈ line-height of body)
 * `circle` avatar / icon placeholder
 */
type SkeletonShape = "block" | "text" | "circle";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shape?: SkeletonShape;
}

export function Skeleton({ className, shape = "block", ...props }: SkeletonProps) {
  return (
    <div
      role="presentation"
      aria-hidden
      className={cn(
        "skeleton-pulse",
        shape === "block" && "rounded-[10px] h-4 w-full",
        shape === "text" && "rounded-[6px] h-3.5 w-full",
        shape === "circle" && "rounded-full size-10",
        className,
      )}
      {...props}
    />
  );
}

/** A vertical stack of text skeletons that resembles a paragraph. */
export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-2", className)} aria-hidden>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          shape="text"
          style={{ width: i === lines - 1 ? "62%" : "100%" }}
        />
      ))}
    </div>
  );
}

/** Card-shaped placeholder for grid loading. */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-[18px] border border-[var(--color-border)] bg-paper-white p-5",
        className,
      )}
      aria-hidden
    >
      <Skeleton shape="block" className="h-5 w-2/3 mb-3" />
      <SkeletonText lines={3} />
      <div className="mt-4 flex gap-2">
        <Skeleton shape="block" className="h-7 w-16" />
        <Skeleton shape="block" className="h-7 w-20" />
      </div>
    </div>
  );
}
