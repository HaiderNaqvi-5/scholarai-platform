type SkeletonProps = {
  width?: string;
  height?: string;
  radius?: string;
  className?: string;
};

export function Skeleton({
  width = "100%",
  height = "1rem",
  radius = "8px",
  className = "",
}: SkeletonProps) {
  return (
    <span
      aria-hidden="true"
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius: radius }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="surface-card" aria-hidden="true">
      <Skeleton width="40%" height="0.7rem" />
      <Skeleton width="70%" height="1.2rem" radius="10px" />
      <Skeleton width="100%" height="0.9rem" />
      <Skeleton width="60%" height="0.9rem" />
    </div>
  );
}

export function SkeletonLine({ count = 3 }: { count?: number }) {
  return (
    <div className="skeleton-lines" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton
          key={i}
          width={i === count - 1 ? "60%" : "100%"}
          height="0.9rem"
        />
      ))}
    </div>
  );
}
