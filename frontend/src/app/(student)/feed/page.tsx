"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { endpoints } from "@/lib/api";
import type { SavedOpportunity } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RecommendationCard } from "@/components/scholarship/RecommendationCard";
import { useAuth } from "@/lib/auth/AuthProvider";

export default function FeedPage() {
  const auth = useAuth();
  const qc = useQueryClient();

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

  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
    enabled: profileQ.isSuccess,
  });
  const savedSet = useMemo(
    () => new Set(savedQ.data?.items.map((s) => s.scholarship_id) ?? []),
    [savedQ.data],
  );

  const toggleSave = useMutation({
    mutationFn: async ({ id, currentlySaved }: { id: string; currentlySaved: boolean }) => {
      if (currentlySaved) await endpoints.saved.remove(id);
      else await endpoints.saved.add(id);
    },
    onMutate: async ({ id, currentlySaved }) => {
      await qc.cancelQueries({ queryKey: ["saved"] });
      const prev = qc.getQueryData<{ items: SavedOpportunity[] }>(["saved"]);
      qc.setQueryData<{ items: SavedOpportunity[] } | undefined>(["saved"], (old) => {
        if (!old) return old;
        if (currentlySaved) return { items: old.items.filter((x) => x.scholarship_id !== id) };
        const sch = recsQ.data?.items.find((r) => r.scholarship.id === id)?.scholarship;
        if (!sch) return old;
        return {
          items: [
            ...old.items,
            {
              scholarship_id: id,
              scholarship: sch,
              status: "saved" as const,
              saved_at: new Date().toISOString(),
            },
          ],
        };
      });
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["saved"], ctx?.prev);
      toast.error("Couldn't update saved list.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["saved"] }),
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
            <Skeleton key={i} className="h-44 w-full" />
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
            <RecommendationCard
              item={rec}
              profile={profileQ.data}
              saved={savedSet.has(rec.scholarship.id)}
              saving={toggleSave.isPending && toggleSave.variables?.id === rec.scholarship.id}
              onToggleSave={() =>
                toggleSave.mutate({
                  id: rec.scholarship.id,
                  currentlySaved: savedSet.has(rec.scholarship.id),
                })
              }
            />
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
