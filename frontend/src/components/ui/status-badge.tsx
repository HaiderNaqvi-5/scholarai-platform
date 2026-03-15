type StatusBadgeVariant = "validated" | "generated" | "planned" | "warning";

type StatusBadgeProps = {
  label: string;
  variant?: StatusBadgeVariant;
};

export function StatusBadge({
  label,
  variant = "planned",
}: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${variant}`}>
      {label}
    </span>
  );
}
