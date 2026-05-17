import { cn } from "@/lib/utils";

/**
 * StatChip — marketing surface ornament. Mono numeral on a paper-white
 * pill with hairline border. Used in landing hero, booth landing, and
 * upgrade page. Stats are decorative — same data must also appear as
 * accessible text in the section copy.
 */
interface StatChipProps {
  value: string | number;
  label: string;
  className?: string;
}

export function StatChip({ value, label, className }: StatChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 py-2",
        className,
      )}
    >
      <span className="font-mono text-[15px] font-semibold tabular-nums text-ink-deep">
        {value}
      </span>
      <span className="text-[13px] text-ink-muted">{label}</span>
    </span>
  );
}
