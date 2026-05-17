"use client";

/**
 * /feed — Dashboard Home (Front-upgrade §6.8).
 *
 * 30-second status read: plan chip, profile-complete card (when <80%),
 * 2×2 action grid (Find matches / Track applications / Draft SOP /
 * Practice visa), recent matches (3 compact), tracker summary (6 stages).
 *
 * Per-screen bans: "Good morning, Aisha! 👋", rotating motivational quote,
 * AI suggestion banner, trophy / streak counter.
 */

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Sparkles,
  KanbanSquare,
  FileSignature,
  Plane,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";
import { endpoints } from "@/lib/api";
import type { SavedOpportunity } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardEyebrow } from "@/components/ui/card";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { useAuth } from "@/lib/auth/AuthProvider";
import { formatDeadline } from "@/lib/utils";
import { cn } from "@/lib/utils";

const TRACKER_STAGES = [
  { key: "wishlist", label: "Wishlist" },
  { key: "preparing", label: "Preparing" },
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "decision", label: "Decision" },
  { key: "accepted", label: "Accepted" },
] as const;

export default function FeedPage() {
  const auth = useAuth();
  const qc = useQueryClient();
  const user = auth.status === "authed" ? auth.user : null;

  const profileQ = useQuery({
    queryKey: ["profile"],
    queryFn: endpoints.profile.get,
    retry: false,
  });

  const recsQ = useQuery({
    queryKey: ["recommendations", "feed-compact"],
    queryFn: () => endpoints.recommendations.build(3),
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

  // Profile completeness heuristic: 7 required fields.
  const profileComplete = useMemo(() => {
    const p = profileQ.data;
    if (!p) return 0;
    const filled = [
      p.citizenship_country_code,
      p.gpa_value,
      p.target_field,
      p.target_degree_level,
      p.target_country_code,
      p.language_test_type,
      p.language_test_score,
    ].filter(Boolean).length;
    return Math.round((filled / 7) * 100);
  }, [profileQ.data]);

  const userName = user?.full_name?.split(" ")[0];
  const expiry = user?.plan_expires_at ?? null;
  const planLabel = usePlanLabel(user?.plan ?? null, expiry);

  if (profileQ.isError) {
    return (
      <div className="mx-auto max-w-[1080px] py-12">
        <EmptyState
          full
          title="Finish your profile to see matches."
          description="Eligibility runs on citizenship and degree level. About two minutes."
          action={
            <Button asChild>
              <Link href="/onboarding">Complete profile</Link>
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1080px] px-6 py-8 md:px-10 md:py-10">
      {/* Page header */}
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <CardEyebrow>Dashboard</CardEyebrow>
          <h1 className="mt-1 font-display text-[32px] italic font-[400] leading-[1.15] tracking-[-0.02em] text-ink-deep">
            {userName ? `Welcome back, ${userName}.` : "Welcome back."}
          </h1>
        </div>
        {planLabel ? (
          <Badge
            tone={user?.plan === "elite" ? "gold" : user?.plan === "pro" ? "lapis" : "neutral"}
          >
            {planLabel}
          </Badge>
        ) : null}
      </header>

      {/* Profile-complete card */}
      {profileQ.data && profileComplete < 80 ? (
        <Card className="mt-6 p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between md:gap-6">
            <div className="flex-1">
              <p className="text-[14px] font-medium text-ink-deep">
                Your profile is{" "}
                <span className="font-mono tabular-nums text-lapis">{profileComplete}%</span>{" "}
                complete. Finish for better matches.
              </p>
              <div className="mt-2 h-1 w-full rounded-full bg-paper-edge">
                <div
                  className="h-full rounded-full bg-lapis transition-all duration-[var(--motion-layout)]"
                  style={{ width: `${profileComplete}%` }}
                />
              </div>
            </div>
            <Button asChild variant="secondary" size="sm">
              <Link href="/profile">Update profile</Link>
            </Button>
          </div>
        </Card>
      ) : null}

      {/* Action 2×2 grid */}
      <section className="mt-8" aria-label="Quick actions">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <ActionTile
            href="/dashboard/scholarships/match"
            icon={<Sparkles className="size-5" strokeWidth={1.5} />}
            label="Find matches"
            body="Score the live catalog against your profile."
          />
          <ActionTile
            href="/tracker"
            icon={<KanbanSquare className="size-5" strokeWidth={1.5} />}
            label="Track applications"
            body="Six-stage Kanban with 14-item checklists."
          />
          <ActionTile
            href="/documents/sop"
            icon={<FileSignature className="size-5" strokeWidth={1.5} />}
            label="Draft SOP"
            body="Pakistan-context, paragraph by paragraph."
          />
          <ActionTile
            href="/interviews/visa"
            icon={<Plane className="size-5" strokeWidth={1.5} />}
            label="Practice visa"
            body="Seventy questions across UK / US / CA / DE."
          />
        </div>
      </section>

      {/* Recent matches */}
      <section className="mt-12" aria-labelledby="recent-matches-h2">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <CardEyebrow>Recent matches</CardEyebrow>
            <h2
              id="recent-matches-h2"
              className="mt-1 font-display text-[22px] italic font-[450] leading-tight text-ink-deep"
            >
              Top picks for you
            </h2>
          </div>
          <Button asChild variant="link">
            <Link href="/dashboard/scholarships/match">
              See all matches → <ArrowRight className="ml-1 size-3.5" strokeWidth={1.5} />
            </Link>
          </Button>
        </div>

        {recsQ.isLoading ? (
          <div className="grid gap-3 md:grid-cols-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : null}

        {recsQ.isError ? (
          <ErrorState
            title="Couldn't load matches."
            description="The ranker is temporarily unavailable."
            action={
              <Button variant="secondary" onClick={() => recsQ.refetch()}>
                Retry
              </Button>
            }
          />
        ) : null}

        {recsQ.data && recsQ.data.items.length === 0 ? (
          <EmptyState
            title="Run your first match. Takes 3 seconds."
            description="Once your profile is in, we'll score live scholarships against it."
            action={
              <Button asChild>
                <Link href="/discover">Browse all</Link>
              </Button>
            }
          />
        ) : null}

        {recsQ.data && recsQ.data.items.length > 0 ? (
          <ul role="list" className="grid gap-3 md:grid-cols-3">
            {recsQ.data.items.slice(0, 3).map((rec) => {
              const isSaved = savedSet.has(rec.scholarship.id);
              const deadline = rec.scholarship.deadline
                ? formatDeadline(rec.scholarship.deadline)
                : null;
              return (
                <li key={rec.scholarship.id}>
                  <Card hoverable className="flex h-full flex-col p-5">
                    <Link
                      href={`/scholarships/${rec.scholarship.id}`}
                      className="flex flex-1 flex-col"
                    >
                      <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                        {rec.scholarship.provider}
                      </p>
                      <h3 className="mt-2 line-clamp-2 text-[15px] font-semibold leading-[1.35] text-ink-deep">
                        {rec.scholarship.title}
                      </h3>
                      {deadline ? (
                        <p
                          className={cn(
                            "mt-4 font-mono text-[12px] tabular-nums",
                            deadline.tone === "urgent" && "text-sindoor",
                            deadline.tone === "soon" && "text-caution",
                            deadline.tone === "ok" && "text-ink-muted",
                            deadline.tone === "passed" && "text-ink-subtle line-through",
                          )}
                        >
                          {deadline.label}
                        </p>
                      ) : null}
                    </Link>
                    <div className="mt-4 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() =>
                          toggleSave.mutate({
                            id: rec.scholarship.id,
                            currentlySaved: isSaved,
                          })
                        }
                        className="text-[12px] text-lapis underline underline-offset-2 hover:decoration-2"
                      >
                        {isSaved ? "Saved" : "Save"}
                      </button>
                      <ArrowRight className="size-3.5 text-ink-muted" strokeWidth={1.5} />
                    </div>
                  </Card>
                </li>
              );
            })}
          </ul>
        ) : null}
      </section>

      {/* Tracker summary */}
      <TrackerSummary />
    </div>
  );
}

/**
 * usePlanLabel — computes the plan chip label client-side so the trial
 * countdown depends on `Date.now()` only after hydration (avoids the
 * react-hooks/purity lint flag).
 */
function usePlanLabel(plan: string | null, expiry: string | null): string | null {
  const [label, setLabel] = useState<string | null>(() => {
    if (!plan) return null;
    if (plan === "free") return "Explorer";
    if (plan === "pro") return expiry ? "Pro trial" : "Pro";
    if (plan === "elite") return "Elite";
    return "Institution";
  });
  useEffect(() => {
    if (plan !== "pro" || !expiry) return;
    const tick = () => {
      const days = Math.max(0, Math.ceil((new Date(expiry).getTime() - Date.now()) / 86_400_000));
      setLabel(`Pro trial — ${days} day${days === 1 ? "" : "s"}`);
    };
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, [plan, expiry]);
  return label;
}

function ActionTile({
  href,
  icon,
  label,
  body,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  body: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col gap-2 rounded-[18px] border border-[var(--color-border)] bg-paper-white p-5 transition-all duration-[var(--motion-micro)] ease-[var(--ease-out)] hover:border-ink-muted/30 hover:shadow-[var(--shadow-lift)] tap-target"
    >
      <span
        aria-hidden
        className="flex size-10 items-center justify-center rounded-[10px] bg-paper-warm text-ink-deep group-hover:bg-lapis-soft group-hover:text-lapis"
      >
        {icon}
      </span>
      <h3 className="mt-2 text-[15px] font-semibold text-ink-deep">{label}</h3>
      <p className="text-[13px] leading-[1.5] text-ink-muted">{body}</p>
      <span className="mt-auto inline-flex items-center gap-1 text-[12px] font-medium text-lapis">
        Open <ArrowRight className="size-3" strokeWidth={1.5} />
      </span>
    </Link>
  );
}

function TrackerSummary() {
  const trackerQ = useQuery({
    queryKey: ["tracker", "summary"],
    queryFn: () => endpoints.tracker.list(),
    retry: false,
  });

  const counts = useMemo(() => {
    const init = Object.fromEntries(TRACKER_STAGES.map((s) => [s.key, 0])) as Record<
      string,
      number
    >;
    if (!trackerQ.data) return init;
    for (const t of trackerQ.data.items ?? []) {
      const k = (t.stage || "").toLowerCase();
      if (k in init) init[k]++;
    }
    return init;
  }, [trackerQ.data]);

  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <section className="mt-12" aria-labelledby="tracker-h2">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <CardEyebrow>Your applications</CardEyebrow>
          <h2
            id="tracker-h2"
            className="mt-1 font-display text-[22px] italic font-[450] leading-tight text-ink-deep"
          >
            Where things stand
          </h2>
        </div>
        <Button asChild variant="link">
          <Link href="/tracker">
            Open tracker → <ArrowRight className="ml-1 size-3.5" strokeWidth={1.5} />
          </Link>
        </Button>
      </div>

      {trackerQ.isLoading ? (
        <Skeleton className="h-24 w-full rounded-[18px]" />
      ) : trackerQ.isError ? (
        <ErrorState
          title="Couldn't load tracker."
          action={
            <Button variant="secondary" size="sm" onClick={() => trackerQ.refetch()}>
              Retry
            </Button>
          }
        />
      ) : total === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="size-7" strokeWidth={1.5} />}
          title="No applications yet."
          description="Add a scholarship to your tracker to see it here."
          action={
            <Button asChild variant="secondary">
              <Link href="/discover">Browse scholarships</Link>
            </Button>
          }
        />
      ) : (
        <Card className="p-5">
          <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {total} application{total === 1 ? "" : "s"}
          </p>
          <ul role="list" className="grid grid-cols-2 gap-3 md:grid-cols-6">
            {TRACKER_STAGES.map((s) => (
              <li key={s.key}>
                <Link
                  href={`/tracker?stage=${s.key}`}
                  className="block rounded-[10px] border border-[var(--color-border-quiet)] bg-paper-warm/40 px-3 py-3 transition-colors hover:bg-paper-warm tap-target"
                >
                  <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                    {s.label}
                  </p>
                  <p className="mt-1 font-mono text-[18px] font-semibold tabular-nums text-ink-deep">
                    {counts[s.key]}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  );
}
