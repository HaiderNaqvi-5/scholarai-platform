"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  SavedOpportunityItem,
  SavedOpportunityListResponse,
  ScholarshipListItem,
  ScholarshipListResponse,
  StudentProfile,
} from "@/lib/types";
import { PulseHeader } from "@/components/dashboard/pulse-header";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

type DashboardDataState = {
  isLoading: boolean;
  error: string | null;
  profile: StudentProfile | null;
  saved: SavedOpportunityItem[];
  published: ScholarshipListItem[];
};

export function DashboardShell() {
  const { accessToken, currentUser } = useAuth();
  const [state, setState] = useState<DashboardDataState>({
    isLoading: true,
    error: null,
    profile: null,
    saved: [],
    published: [],
  });

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadDashboard = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      const [profileResult, savedResult, publishedResult] = await Promise.allSettled([
        apiRequest<StudentProfile>("/profile", { token: accessToken }),
        apiRequest<SavedOpportunityListResponse>("/saved-opportunities", {
          token: accessToken,
        }),
        apiRequest<ScholarshipListResponse>("/scholarships?page=1&page_size=4", {
          token: accessToken,
        }),
      ]);

      if (!isActive) {
        return;
      }

      const nextState: DashboardDataState = {
        isLoading: false,
        error: null,
        profile: null,
        saved: [],
        published: [],
      };

      if (profileResult.status === "fulfilled") {
        nextState.profile = profileResult.value;
      } else if (!is404(profileResult.reason)) {
        nextState.error = profileResult.reason.message;
      }

      if (savedResult.status === "fulfilled") {
        nextState.saved = savedResult.value.items;
      } else if (!nextState.error) {
        nextState.error = savedResult.reason.message;
      }

      if (publishedResult.status === "fulfilled") {
        nextState.published = publishedResult.value.items;
      } else if (!nextState.error) {
        nextState.error = publishedResult.reason.message;
      }

      setState(nextState);
    };

    void loadDashboard();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const savedIds = useMemo(
    () => new Set(state.saved.map((item) => item.scholarship_id)),
    [state.saved],
  );

  const profileReady = Boolean(state.profile);

  const handleSave = async (scholarshipId: string) => {
    if (!accessToken) {
      return;
    }

    const savedItem = await apiRequest<SavedOpportunityItem>(
      `/saved-opportunities/${scholarshipId}`,
      {
        method: "POST",
        token: accessToken,
      },
    );

    setState((current) => ({
      ...current,
      saved: [
        savedItem,
        ...current.saved.filter((item) => item.scholarship_id !== scholarshipId),
      ],
    }));
  };

  const handleUnsave = async (scholarshipId: string) => {
    if (!accessToken) {
      return;
    }

    await apiRequest<void>(`/saved-opportunities/${scholarshipId}`, {
      method: "DELETE",
      token: accessToken,
    });

    setState((current) => ({
      ...current,
      saved: current.saved.filter((item) => item.scholarship_id !== scholarshipId),
    }));
  };

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <AppShell
      title="Dashboard"
      description="ScholarAI Pulse"
      hideHeader
    >
      <PulseHeader 
        name={currentUser?.full_name} 
        savedCount={state.saved.length} 
        profileReady={profileReady} 
      />

      {state.error ? (
        <section className="glass-surface p-6 mb-8 border-coral-600/20 bg-coral-600/5" data-testid="dashboard-error">
          <PageHeader
            eyebrow="Alert"
            title="System Connection Issue"
            description={state.error}
          />
        </section>
      ) : null}

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-12"
      >
        <section className="dashboard-grid">
          <motion.article variants={item} className="glass-surface p-8" data-testid="profile-summary">
            <PageHeader
              eyebrow="Intelligence Profile"
              title="Identity & Targets"
              description="Refined data for personalized matching."
            />
            {state.isLoading ? (
              <div className="space-y-4 pt-6">
                <SkeletonLine count={3} />
              </div>
            ) : state.profile ? (
              <div className="space-y-6 pt-6">
                <div className="grid gap-4">
                  <div className="flex justify-between items-center py-3 border-b border-white/5">
                    <span className="text-sm text-neutral-500">Academic Target</span>
                    <span className="text-sm font-semibold text-neutral-900">{state.profile.target_degree_level} · {state.profile.target_field}</span>
                  </div>
                  <div className="flex justify-between items-center py-3 border-b border-white/5">
                    <span className="text-sm text-neutral-500">Destination</span>
                    <span className="text-sm font-semibold text-neutral-900">{state.profile.target_country_code}</span>
                  </div>
                  <div className="flex justify-between items-center py-3 border-b border-white/5">
                    <span className="text-sm text-neutral-500">Academic Standing</span>
                    <span className="text-sm font-semibold text-neutral-900">{state.profile.gpa_value ?? "—"} / {state.profile.gpa_scale} GPA</span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Link className="nav-link !rounded-xl" href="/profile">
                    Edit Profile
                  </Link>
                  <Link className="auth-link auth-link--primary !rounded-xl" href="/recommendations">
                    View Matches
                  </Link>
                </div>
              </div>
            ) : (
              <EmptyState
                title="Profile Lockdown"
                description="Your intelligence profile is incomplete. This restricts personalized matching."
                action={
                  <Link className="auth-link auth-link--primary" href="/onboarding">
                    Complete Identity
                  </Link>
                }
              />
            )}
          </motion.article>

          <motion.article variants={item} className="glass-surface p-8" data-testid="saved-opportunities">
            <PageHeader
              eyebrow="Shortlist"
              title="Active Opportunities"
              description="Track deadlines and preparation readiness."
            />
            {state.isLoading ? (
              <div className="pt-6 space-y-4">
                <SkeletonCard />
              </div>
            ) : state.saved.length > 0 ? (
              <div className="opportunity-list pt-6">
                {state.saved.map((item) => (
                  <article className="p-4 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-all group" key={item.scholarship_id}>
                    <div className="flex justify-between items-start mb-2">
                       <h3 className="font-semibold text-neutral-900 group-hover:text-cobalt-600 transition-colors">{item.title}</h3>
                       <StatusBadge label="Saved" variant="validated" />
                    </div>
                    <p className="text-xs text-neutral-500 mb-4 uppercase tracking-wider">
                      {item.provider_name} · {item.country_code}
                    </p>
                    <div className="flex gap-2">
                      <Link className="text-xs font-bold text-neutral-400 hover:text-neutral-900 transition-all" href={`/scholarships/${item.scholarship_id}`}>
                        View Details
                      </Link>
                      <button
                        className="text-xs font-bold text-coral-600 opacity-60 hover:opacity-100 transition-all"
                        onClick={() => void handleUnsave(item.scholarship_id)}
                        type="button"
                      >
                        Remove
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                title="Empty Vault"
                description="Save opportunities from the discovery engine to track them here."
                action={
                  <Link className="auth-link auth-link--primary" href="/scholarships">
                    Launch Discovery
                  </Link>
                }
              />
            )}
          </motion.article>
        </section>

        <motion.section variants={item} className="glass-surface p-10">
          <PageHeader
            eyebrow="Preparation Hub"
            title="Accelerate Your Applications"
            description="Use AI-driven feedback and practice to increase your fit scores."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <EntryCard
              href="/recommendations"
              label="Intelligent Matches"
              description="XGBoost ranked opportunities tailored to your targets."
            />
            <EntryCard
              href="/document-feedback"
              label="Document Lab"
              description="Grounded writing assistance for statements and prompts."
            />
            <EntryCard
              href="/interview"
              label="Interview Forge"
              description="Practice sessions with live probing and rubric scoring."
            />
          </div>
        </motion.section>

        <motion.section variants={item} className="glass-surface p-10" data-testid="published-opportunities">
          <div className="flex items-end justify-between mb-8">
              <PageHeader
                eyebrow="Global Discovery"
                title="Recent Additions"
                description="New opportunities synced from the ingestion pipeline."
              />
              <Link href="/scholarships" className="text-sm font-bold text-cobalt-600 hover:underline">
                Browse Repository →
              </Link>
          </div>
          {state.isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
            </div>
          ) : state.published.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {state.published.map((item) => {
                const isSaved = savedIds.has(item.scholarship_id);
                return (
                  <article className="p-6 rounded-2xl border border-white/5 bg-white/5 hover:border-cobalt-600/30 transition-all flex flex-col justify-between" key={item.scholarship_id}>
                    <div>
                        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-3">
                            {item.country_code} · {item.deadline_at ? new Date(item.deadline_at).toLocaleDateString() : 'No Deadline'}
                        </div>
                        <h3 className="text-lg font-semibold text-neutral-900 leading-snug mb-2">{item.title}</h3>
                        <p className="text-xs text-neutral-500 line-clamp-2">{item.provider_name}</p>
                    </div>
                    <div className="mt-8 flex gap-3">
                      <button
                        className={`flex-1 text-xs font-bold py-2.5 rounded-lg transition-all ${isSaved ? 'bg-neutral-100 text-neutral-500' : 'bg-neutral-900 text-white hover:bg-black'}`}
                        onClick={() =>
                          void (isSaved
                            ? handleUnsave(item.scholarship_id)
                            : handleSave(item.scholarship_id))
                        }
                        type="button"
                      >
                        {isSaved ? "Saved" : "Save Opportunity"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="p-12 text-center border-2 border-dashed border-white/10 rounded-3xl">
              <p className="text-neutral-400 font-medium">
                Syncing global repository... No new records found in current batch.
              </p>
            </div>
          )}
        </motion.section>
      </motion.div>
    </AppShell>
  );
}

function EntryCard({
  href,
  label,
  description,
}: {
  href: string;
  label: string;
  description: string;
}) {
  return (
    <Link href={href} className="group p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-cobalt-600/50 hover:bg-white/10 transition-all flex flex-col gap-4">
      <div className="w-10 h-10 rounded-xl bg-cobalt-600/10 flex items-center justify-center text-cobalt-600 group-hover:scale-110 transition-transform">
          <Activity size={20} />
      </div>
      <div>
        <h3 className="font-bold text-lg text-neutral-900">{label}</h3>
        <p className="text-sm text-neutral-500 leading-relaxed mt-1">{description}</p>
      </div>
    </Link>
  );
}
function is404(error: unknown): error is ApiError {
  return (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    (error as ApiError).status === 404
  );
}
