"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, ArrowRight } from "lucide-react";
import { endpoints } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth/AuthProvider";
import { formatAmount, formatDeadline } from "@/lib/utils";

export default function FeedPage() {
  const auth = useAuth();
  const profileQ = useQuery({
    queryKey: ["profile"],
    queryFn: endpoints.profile.get,
    retry: false,
  });
  const recsQ = useQuery({
    queryKey: ["recommendations", "feed"],
    queryFn: () => endpoints.recommendations.build(10),
    enabled: profileQ.isSuccess,
  });

  const userName = auth.status === "authed" ? auth.user.full_name?.split(" ")[0] : null;

  if (profileQ.isError) {
    return (
      <EmptyState
        title="Finish your profile to see matches"
        body="Eligibility runs on citizenship and degree level. Two minutes."
        cta={{ href: "/onboarding", label: "Complete profile" }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <header className="mb-6">
        <h1 className="font-display text-3xl text-ink">
          {userName ? `Hi, ${userName}.` : "Your matches"}
        </h1>
        <p className="mt-1 text-ink-muted">
          {recsQ.data
            ? `Ranking ${recsQ.data.items.length} scholarships against your profile.`
            : "Ranking scholarships against your profile."}
        </p>
      </header>

      {recsQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : null}

      {recsQ.isError ? (
        <EmptyState
          title="Couldn't load matches."
          body="The ranker is temporarily unavailable."
          cta={{ onClick: () => recsQ.refetch(), label: "Retry" }}
        />
      ) : null}

      {recsQ.data && recsQ.data.items.length === 0 ? (
        <EmptyState
          title="No matches yet"
          body="Try widening your fields, or browse all open scholarships."
          cta={{ href: "/discover", label: "Browse all" }}
        />
      ) : null}

      <ul className="space-y-3">
        {recsQ.data?.items.map((rec) => (
          <li key={rec.scholarship.id}>
            <RecommendationRow item={rec} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function RecommendationRow({ item }: { item: NonNullable<ReturnType<typeof useQuery>["data"]> extends infer T ? T : never }) {
  // typed inline to avoid pulling type re-export
  const rec = item as unknown as import("@/lib/api").RecommendationItem;
  const s = rec.scholarship;
  const dl = s.deadline ? formatDeadline(s.deadline) : null;
  return (
    <Card className="hover:border-ink-muted">
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="flex-1">
          <CardTitle>
            <Link href={`/scholarships/${s.id}`} className="hover:underline underline-offset-4">
              {s.title}
            </Link>
          </CardTitle>
          <p className="mt-1 text-sm text-ink-muted">
            {s.provider} · {s.country_code}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {dl ? (
            <Badge tone={dl.tone === "urgent" ? "caution" : dl.tone === "passed" ? "danger" : "neutral"}>
              {dl.label}
            </Badge>
          ) : null}
          <span className="font-mono text-sm text-ink">
            {formatAmount(s.amount_max ?? s.amount_min, s.currency || "CAD")}
          </span>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {rec.stages.map((stage) => (
            <Badge key={stage.name} tone={stage.status === "passed" || stage.status === "applied" ? "validated" : "neutral"}>
              {stage.name}
            </Badge>
          ))}
        </div>
        {(rec.supporting_factors?.length ?? 0) > 0 ? (
          <FactorList tone="validated" label="Supports" factors={rec.supporting_factors} />
        ) : null}
        {(rec.limiting_factors?.length ?? 0) > 0 ? (
          <FactorList tone="caution" label="Limits" factors={rec.limiting_factors} />
        ) : null}
        <p className="flex items-center gap-1.5 text-xs text-ink-subtle">
          <Sparkles className="size-3" strokeWidth={2} aria-hidden /> Ranked from your profile and
          published eligibility rules.
        </p>
      </CardBody>
    </Card>
  );
}

function FactorList({ tone, label, factors }: { tone: "validated" | "caution"; label: string; factors: string[] }) {
  return (
    <div className="text-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-ink-subtle">{label}</p>
      <ul className="mt-1 space-y-1">
        {factors.map((f, i) => (
          <li
            key={i}
            className={`pl-3 ${tone === "validated" ? "validated-stripe" : "caution-stripe"}`}
          >
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EmptyState({
  title,
  body,
  cta,
}: {
  title: string;
  body: string;
  cta?: { href?: string; label: string; onClick?: () => void };
}) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <p className="mt-2 text-ink-muted">{body}</p>
      {cta ? (
        <div className="mt-5">
          {cta.href ? (
            <Button asChild>
              <Link href={cta.href}>
                {cta.label} <ArrowRight className="size-4" strokeWidth={2} />
              </Link>
            </Button>
          ) : (
            <Button onClick={cta.onClick}>{cta.label}</Button>
          )}
        </div>
      ) : null}
    </div>
  );
}
