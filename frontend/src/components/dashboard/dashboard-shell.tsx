"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
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

  return (
    <AppShell
      eyebrow="Dashboard"
      title="Your scholarship workspace keeps profile, saved opportunities, and next actions in one place."
      description="This dashboard is intentionally compact. It helps you stay oriented without turning the product into a noisy control panel."
      intro={
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="Account active" variant="validated" />
            <StatusBadge
              label={profileReady ? "Profile ready" : "Profile needed"}
              variant={profileReady ? "generated" : "warning"}
            />
          </div>
          <p className="body-copy">
            {currentUser?.full_name
              ? `${currentUser.full_name}, your next useful actions are queued below.`
              : "Your next useful actions are queued below."}
          </p>
        </div>
      }
    >
      {state.error ? (
        <section className="surface-card" data-testid="dashboard-error">
          <PageHeader
            eyebrow="Workspace status"
            title="The dashboard needs attention."
            description={state.error}
          />
        </section>
      ) : null}

      <section className="metrics-grid" data-testid="dashboard-shell">
        <article className="data-point">
          <p className="data-point__label">Saved opportunities</p>
          <strong>{state.saved.length}</strong>
          <p className="body-copy">Shortlist items tied to published scholarship records.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Profile status</p>
          <strong>{profileReady ? "Complete enough to rank" : "Needs first pass"}</strong>
          <p className="body-copy">Recommendations become more useful once the profile is saved.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Next preparation tools</p>
          <strong>Documents and interview</strong>
          <p className="body-copy">Both tools stay bounded and clearly separate from scholarship facts.</p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card" data-testid="profile-summary">
          <PageHeader
            eyebrow="Profile summary"
            title="The profile behind your shortlist"
            description="ScholarAI shows the exact information driving eligibility-aware ranking so the recommendation path stays inspectable."
          />
          {state.isLoading ? (
            <p className="body-copy">Loading your saved profile.</p>
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
                <p className="list-heading">Eligibility anchors</p>
                <p className="body-copy">
                  Citizenship {state.profile.citizenship_country_code}, GPA{" "}
                  {state.profile.gpa_value ?? "not set"} / {state.profile.gpa_scale}
                </p>
              </article>
              <div className="dashboard-actions">
                <Link className="nav-link" href="/profile">
                  Review profile
                </Link>
                <Link className="auth-link auth-link--primary" href="/recommendations">
                  Open recommendations
                </Link>
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Start with the first-run profile so ScholarAI can explain why a
                published opportunity belongs on your shortlist.
              </p>
              <Link className="auth-link auth-link--primary" href="/onboarding">
                Start onboarding
              </Link>
            </div>
          )}
        </article>

        <article className="surface-panel" data-testid="saved-opportunities">
          <PageHeader
            eyebrow="Saved opportunities"
            title="Your current shortlist"
            description="Saved opportunities stay close to the dashboard so the workspace feels focused instead of scattered across extra routes."
          />
          {state.isLoading ? (
            <p className="body-copy">Loading saved opportunities.</p>
          ) : state.saved.length > 0 ? (
            <div className="opportunity-list">
              {state.saved.map((item) => (
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
                      type="button"
                    >
                      Remove
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                Nothing is saved yet. Start with the published catalog, then keep your
                shortlist here while you compare fit and timing.
              </p>
              <Link className="nav-link" href="/scholarships">
                Browse scholarships
              </Link>
            </div>
          )}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Next actions"
          title="Move from exploration to preparation"
          description="Each workspace below has a clear purpose so the product feels structured rather than stacked with tools."
        />
        <div className="dashboard-grid dashboard-grid--tight">
          <EntryCard
            href="/recommendations"
            label="Recommendations"
            description="Review fit, caution notes, and why each opportunity surfaced."
          />
          <EntryCard
            href="/document-feedback"
            label="Document workspace"
            description="Work on one draft at a time with bounded, structured writing guidance."
          />
          <EntryCard
            href="/interview"
            label="Interview practice"
            description="Practice one structured response at a time with rubric-based feedback."
          />
        </div>
      </section>

      <section className="surface-card" data-testid="published-opportunities">
        <PageHeader
          eyebrow="Suggested published records"
          title="Keep discovery close to the workspace"
          description="A compact set of published records makes it easy to add a shortlist item without leaving the dashboard."
        />
        {state.isLoading ? (
          <p className="body-copy">Loading published opportunities.</p>
        ) : state.published.length > 0 ? (
          <div className="opportunity-list">
            {state.published.map((item) => {
              const isSaved = savedIds.has(item.scholarship_id);
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
                      type="button"
                    >
                      {isSaved ? "Saved" : "Save opportunity"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-panel">
            <p className="body-copy">
              No published scholarships are currently available in the local dataset.
              Once records are published, this area becomes a quick shortlist entry point.
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
      <StatusBadge label="Workspace" variant="neutral" />
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
