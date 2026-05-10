import Link from "next/link";
import { Construction } from "lucide-react";
import { Button } from "@/components/ui/button";

export function PlaceholderRoute({
  title,
  blurb,
  sprint,
}: {
  title: string;
  blurb: string;
  sprint: string;
}) {
  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10">
        <Construction className="size-6 text-ink-muted" strokeWidth={1.5} aria-hidden />
        <h1 className="mt-4 font-display text-2xl text-ink">{title}</h1>
        <p className="mt-2 text-ink-muted">{blurb}</p>
        <p className="mt-4 font-mono text-xs uppercase tracking-wider text-ink-subtle">
          Lands in {sprint}
        </p>
        <div className="mt-6">
          <Button asChild variant="secondary">
            <Link href="/feed">Back to your matches</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
