"use client";

/**
 * /scholarships — Pakistan-pivot personalised match list (PRD §5).
 *
 * Consumes POST /scholarships/match. The endpoint returns a neutral
 * `MatchResponse { items, unlock_offer }` — no internal bucket vocabulary
 * is exposed. Free-tier rows past the visible window arrive with
 * `locked=true` and blank identifiers; they render as a blurred placeholder
 * with an upgrade CTA. When `unlock_offer != null`, a quiet upgrade nudge
 * follows the list using the offer's own headline + message.
 */

import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import { toast } from "sonner";

import { CompatibilityMeter } from "@/components/CompatibilityMeter";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, endpoints } from "@/lib/api";
import type {
  MatchResponse,
  ScholarshipMatchOut,
  UnlockOffer,
} from "@/lib/api";

export default function ScholarshipsPage() {
  const matchQ = useQuery({
    queryKey: ["scholarships", "match"],
    queryFn: () => endpoints.scholarshipMatch.match({}),
    staleTime: 60_000,
  });

  const refresh = useMutation({
    mutationFn: () => endpoints.scholarshipMatch.match({}),
    onSuccess: () => matchQ.refetch(),
    onError: (err) => {
      const msg = err instanceof ApiError ? err.message : "Couldn't refresh.";
      toast.error(msg);
    },
  });

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <PageHeader
        onRefresh={() => refresh.mutate()}
        refreshing={refresh.isPending || matchQ.isFetching}
      />

      {matchQ.isLoading && <ListSkeleton />}

      {matchQ.isError && (
        <ErrorBlock
          message="Couldn't load your matches."
          onRetry={() => matchQ.refetch()}
        />
      )}

      {matchQ.data && <MatchList data={matchQ.data} />}
    </div>
  );
}

function PageHeader({
  onRefresh,
  refreshing,
}: {
  onRefresh: () => void;
  refreshing: boolean;
}) {
  return (
    <header className="mb-6 flex items-end justify-between gap-4">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Your matches
        </p>
        <h1 className="mt-1 font-display text-2xl text-ink">
          Scholarships compatible with your profile
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Ranked by fit against your CGPA, target degree, fields, and country.
        </p>
      </div>
      <Button
        type="button"
        variant="secondary"
        onClick={onRefresh}
        loading={refreshing}
      >
        <RefreshCcw className="size-4" aria-hidden />
        Refresh
      </Button>
    </header>
  );
}

function MatchList({ data }: { data: MatchResponse }) {
  if (data.items.length === 0) {
    return (
      <Card>
        <CardBody className="py-10 text-center">
          <p className="text-ink">No matches yet.</p>
          <p className="mt-1 text-sm text-ink-muted">
            Complete your{" "}
            <Link href="/profile" className="underline-offset-4 hover:underline">
              profile
            </Link>{" "}
            so we can score scholarships against it.
          </p>
        </CardBody>
      </Card>
    );
  }
  return (
    <>
      <ul className="grid gap-3 md:grid-cols-2">
        {data.items.map((row, i) => (
          <li key={row.id ?? `locked-${i}`}>
            <MatchCard row={row} />
          </li>
        ))}
      </ul>

      {data.unlock_offer && <UnlockBlock offer={data.unlock_offer} />}
    </>
  );
}

function MatchCard({ row }: { row: ScholarshipMatchOut }) {
  if (row.locked) {
    return (
      <div className="relative overflow-hidden rounded-[16px] border border-[var(--color-border)] bg-paper-white p-4">
        <div className="pointer-events-none select-none">
          <p className="font-display text-lg text-ink blur-sm">
            {"█".repeat(14)}
          </p>
          <p className="mt-1 text-sm text-ink-muted blur-sm">
            {"█".repeat(8)}
          </p>
          <div className="mt-2">
            <CompatibilityMeter value={row.compatibility} />
          </div>
        </div>
        <div className="absolute inset-0 grid place-items-center bg-ink/5">
          <Button asChild>
            <Link href="/upgrade?plan=elite">Unlock with Elite</Link>
          </Button>
        </div>
      </div>
    );
  }
  return (
    <div className="rounded-[16px] border border-[var(--color-border)] bg-paper-white p-4">
      <p className="font-display text-lg text-ink">{row.name}</p>
      <p className="text-sm text-ink-muted">{row.provider}</p>
      <div className="mt-2">
        <CompatibilityMeter value={row.compatibility} />
      </div>
      <p className="mt-2 text-xs text-ink-muted">
        {row.deadline ? `Deadline ${row.deadline}` : "Deadline TBA"}
        {row.funding_amount ? ` · ${row.funding_amount}` : ""}
      </p>
      {row.id && (
        <div className="mt-3">
          <Button asChild variant="secondary" className="w-full">
            <Link href={`/scholarships/${row.id}`}>View details</Link>
          </Button>
        </div>
      )}
    </div>
  );
}

function UnlockBlock({ offer }: { offer: UnlockOffer }) {
  return (
    <aside className="mt-8 rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
        {offer.locked_count} more reserved
      </p>
      <h2 className="mt-1 font-display text-xl text-ink">{offer.headline}</h2>
      <p className="mt-2 text-sm text-ink-muted">{offer.message}</p>
      <div className="mt-4">
        <Button asChild>
          <Link href={`/upgrade?plan=${offer.to_plan}`}>
            Upgrade to {offer.to_plan === "elite" ? "Elite" : "Pro"} →
          </Link>
        </Button>
      </div>
    </aside>
  );
}

function ListSkeleton() {
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i}>
          <Skeleton className="h-36 w-full" />
        </li>
      ))}
    </ul>
  );
}

function ErrorBlock({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{message}</CardTitle>
      </CardHeader>
      <CardBody>
        <Button onClick={onRetry} variant="secondary">
          Retry
        </Button>
      </CardBody>
    </Card>
  );
}
