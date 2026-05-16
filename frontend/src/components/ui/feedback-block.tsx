import { cn } from "@/lib/utils";

type Tone = "ok" | "warn" | "danger" | "ink";

const TONE_BG: Record<Tone, string> = {
  ok: "bg-[var(--color-validated-soft)]",
  warn: "bg-[var(--color-caution-soft)]",
  danger: "bg-[var(--color-danger-soft)]",
  ink: "bg-paper-warm",
};

/**
 * Coloured eyebrow + body block used by SOP line-feedback and visa-interview
 * feedback panel. Tones map to the design-token soft variants.
 */
export function FeedbackBlock({
  tone,
  title,
  icon,
  children,
  className,
}: {
  tone: Tone;
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-[12px] p-3 text-sm text-ink", TONE_BG[tone], className)}>
      <p className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide text-ink-muted">
        {icon}
        {title}
      </p>
      <div className="mt-1">{children}</div>
    </div>
  );
}
