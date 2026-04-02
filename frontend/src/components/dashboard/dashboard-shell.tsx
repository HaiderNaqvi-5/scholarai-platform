"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { FeedbackNotice } from "@/components/ui/feedback-state";
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

type DashboardDataState = {
  isLoading: boolean;
  error: string | null;
  profile: StudentProfile | null;
  saved: SavedOpportunityItem[];
  published: ScholarshipListItem[];
};

export function DashboardShell() {
  const { accessToken, currentUser } = useAuth();
  const [pendingActionByScholarshipId, setPendingActionByScholarshipId] = useState<
    Record<string, "save" | "unsave" | undefined>
  >({});
  const [actionFeedback, setActionFeedback] = useState<{
    message: string;
    variant: "error" | "success";
  } | null>(null);
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
        apiRequest<StudentProfile>("/profiles", { token: accessToken }),
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

    setPendingActionByScholarshipId((current) => ({ ...current, [scholarshipId]: "save" }));
    setActionFeedback(null);

    try {
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
      setActionFeedback({ message: "Scholarship saved.", variant: "success" });
    } catch (error) {
      setActionFeedback({
        message: getApiErrorMessage(error, "Unable to save scholarship right now."),
        variant: "error",
      });
    } finally {
      setPendingActionByScholarshipId((current) => ({ ...current, [scholarshipId]: undefined }));
    }
  };

  const handleUnsave = async (scholarshipId: string) => {
    if (!accessToken) {
      return;
    }

    setPendingActionByScholarshipId((current) => ({ ...current, [scholarshipId]: "unsave" }));
    setActionFeedback(null);

    try {
      await apiRequest<void>(`/saved-opportunities/${scholarshipId}`, {
        method: "DELETE",
        token: accessToken,
      });

      setState((current) => ({
        ...current,
        saved: current.saved.filter((item) => item.scholarship_id !== scholarshipId),
      }));
      setActionFeedback({
        message: "Scholarship removed from saved opportunities.",
        variant: "success",
      });
    } catch (error) {
      setActionFeedback({
        message: getApiErrorMessage(error, "Unable to remove scholarship right now."),
        variant: "error",
      });
    } finally {
      setPendingActionByScholarshipId((current) => ({ ...current, [scholarshipId]: undefined }));
    }
  };

  return (
    <AppShell
      eyebrow="Dashboard"
      title={
        currentUser?.full_name
          ? `Welcome back, ${currentUser.full_name}.`
          : "Your scholarship workspace."
      }
      description="Profile status, saved opportunities, and next steps — all in one place."
      intro={
        <div className="meta-row">
          <StatusBadge label="Account active" variant="validated" />
          <StatusBadge
            label={profileReady ? "Profile ready" : "Profile needed"}
            variant={profileReady ? "generated" : "warning"}
          />
        </div>
      }
    >
      {state.error ? (
        <section className="surface-card" data-testid="dashboard-error">
          <PageHeader
            eyebrow="Status"
            title="Something went wrong."
            description={state.error}
          />
        </section>
      ) : null}
      {actionFeedback ? (
        <FeedbackNotice message={actionFeedback.message} variant={actionFeedback.variant} />
      ) : null}

      <section className="metrics-grid" data-testid="dashboard-shell">
        <article className="data-point">
          <p className="data-point__label">Saved</p>
          <strong>{state.saved.length}</strong>
          <p className="body-copy">Opportunities on your shortlist.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Profile</p>
          <strong>{profileReady ? "Ready" : "Incomplete"}</strong>
          <p className="body-copy">
            {profileReady
              ? "Recommendations are personalized to your profile."
              : "Complete your profile to unlock recommendations."}
          </p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Preparation</p>
          <strong>Documents & Interview</strong>
          <p className="body-copy">Writing feedback and practice scoring available.</p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card" data-testid="profile-summary">
          <PageHeader
            eyebrow="Profile"
            title="Your recommendation inputs"
            description="The profile data used to rank and explain scholarship matches."
          />
          {state.isLoading ? (
            <div className="surface-list">
              <SkeletonLine count={3} />
              <SkeletonLine count={2} />
            </div>
          ) : state.profile ? (
            <div className="surface-list">
              <article>
                <p className="list-heading">Academic target</p>
                <p className="body-copy">
                  {state.profile.target_degree_level} in {state.profile.target_field} for{" "}
                  {state.profile.target_country_code}
                </p>
              </article>
              <article>
                <p className="list-heading">Eligibility</p>
                <p className="body-copy">
                  Citizenship {state.profile.citizenship_country_code}, GPA{" "}
                  {state.profile.gpa_value ?? "not set"} / {state.profile.gpa_scale}
                </p>
              </article>
              <div className="dashboard-actions">
                <Link className="nav-link" href="/profile">
                  Edit profile
                </Link>
                <Link className="auth-link auth-link--primary" href="/recommendations">
                  View recommendations
                </Link>
              </div>
            </div>
          ) : (
            <EmptyState
              title="Profile incomplete"
              description="Set up your profile so GrantPath AI can explain why scholarships match your background."
              action={
                <Link className="auth-link auth-link--primary" href="/onboarding">
                  Complete profile
                </Link>
              }
            />
          )}
        </article>

        <article className="surface-panel" data-testid="saved-opportunities">
          <PageHeader
            eyebrow="Shortlist"
            title="Saved opportunities"
            description="Scholarships you&apos;re tracking for deadlines and follow-up."
          />
          {state.isLoading ? (
            <div className="opportunity-list">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : state.saved.length > 0 ? (
            <div className="opportunity-list">
              {state.saved.map((item) => {
                const pendingAction = pendingActionByScholarshipId[item.scholarship_id];
                const isPending = Boolean(pendingAction);
                return (
                  <article className="opportunity-card" key={item.scholarship_id}>
                    <div className="meta-row">
                      <StatusBadge label="Published" variant="validated" />
                      <span className="route-card__label">
                        Saved {new Date(item.saved_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="route-card__title">{item.title}</h3>
                    <p className="route-card__description">
                      {item.provider_name ?? "Provider not listed"} · {item.country_code}
                    </p>
                    <div className="dashboard-actions">
                      <Link className="nav-link" href={`/scholarships/${item.scholarship_id}`}>
                        View details
                      </Link>
                      <button
                        className="auth-link auth-link--secondary"
                        onClick={() => void handleUnsave(item.scholarship_id)}
                        disabled={isPending}
                        type="button"
                      >
                        {pendingAction === "unsave" ? "Removing..." : "Remove"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No saved items"
              description="Explore the catalog and save scholarships to track them here."
              action={
                <Link className="auth-link auth-link--primary" href="/scholarships">
                  Browse catalog
                </Link>
              }
            />
          )}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Next steps"
          title="Continue your workflow"
          description="Pick up where you left off across recommendations, writing, and interview practice."
        />
        <div className="dashboard-grid dashboard-grid--tight">
          <EntryCard
            href="/recommendations"
            label="Recommendations"
            description="Review scholarship matches ranked by your profile."
          />
          <EntryCard
            href="/document-feedback"
            label="Documents"
            description="Get structured feedback on application writing."
          />
          <EntryCard
            href="/interview"
            label="Interview"
            description="Practice responses with rubric-based scoring."
          />
        </div>
      </section>

      <section className="surface-card" data-testid="published-opportunities">
        <PageHeader
          eyebrow="Explore"
          title="Recently published scholarships"
          description="Quick access to new opportunities without leaving the dashboard."
        />
        {state.isLoading ? (
          <p className="body-copy">Loading scholarships…</p>
        ) : state.published.length > 0 ? (
          <div className="opportunity-list">
            {state.published.map((item) => {
              const isSaved = savedIds.has(item.scholarship_id);
              const pendingAction = pendingActionByScholarshipId[item.scholarship_id];
              const isPending = Boolean(pendingAction);
              return (
                <article className="opportunity-card" key={item.scholarship_id}>
                  <div className="meta-row">
                    <StatusBadge label="Published" variant="validated" />
                    <span className="route-card__label">
                      {item.deadline_at
                        ? `Deadline ${new Date(item.deadline_at).toLocaleDateString()}`
                        : "Deadline not listed"}
                    </span>
                  </div>
                  <h3 className="route-card__title">{item.title}</h3>
                  <p className="route-card__description">
                    {item.provider_name ?? "Provider not listed"} · {item.country_code}
                  </p>
                  <div className="dashboard-actions">
                    <Link className="nav-link" href={`/scholarships/${item.scholarship_id}`}>
                      View details
                    </Link>
                    <button
                      className={
                        isSaved
                          ? "auth-link auth-link--secondary"
                          : "auth-link auth-link--primary"
                      }
                      onClick={() =>
                        void (isSaved
                          ? handleUnsave(item.scholarship_id)
                          : handleSave(item.scholarship_id))
                      }
                      disabled={isPending}
                      type="button"
                    >
                      {pendingAction === "save"
                        ? "Saving..."
                        : pendingAction === "unsave"
                          ? "Removing..."
                          : isSaved
                            ? "Saved"
                            : "Save"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-panel">
            <p className="body-copy">
              No published scholarships in the current dataset. Check back as new records are added.
            </p>
          </div>
        )}
      </section>
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
    <article className="route-card">
      <h3 className="route-card__title">{label}</h3>
      <p className="route-card__description">{description}</p>
      <Link className="nav-link" href={href}>
        Open
      </Link>
    </article>
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

function getApiErrorMessage(error: unknown, fallback: string) {
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof (error as { message: unknown }).message === "string"
  ) {
    return (error as { message: string }).message;
  }
  return fallback;
}
