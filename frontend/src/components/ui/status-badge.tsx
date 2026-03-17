type StatusBadgeVariant =
  | "validated"
  | "generated"
  | "planned"
  | "warning"
  | "neutral";

type StatusBadgeProps = {
  label: string;
  variant?: StatusBadgeVariant;
};

export function StatusBadge({
  label,
  variant = "neutral",
}: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${variant}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
