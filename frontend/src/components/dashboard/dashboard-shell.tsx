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
        apiRequest<ScholarshipListItem[]>("/scholarships?limit=6", {
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
        nextState.published = publishedResult.value;
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
      title="Dashboard keeps the authenticated workspace calm, focused, and tied to published scholarship records."
      description="This slice adds the minimum useful account flow, saved opportunities, and workspace navigation without pulling in advanced recommendation or document systems."
      eyebrow="Authenticated workspace"
    >
      <section className="dashboard-hero" data-testid="dashboard-shell">
        <div className="dashboard-hero__intro">
          <p className="section-eyebrow">Workspace</p>
          <h2 className="section-title">
            {currentUser?.full_name
              ? `${currentUser.full_name}, your next scholarship actions are organized here.`
              : "Your scholarship workspace is ready."}
          </h2>
          <p className="body-copy">
            Saved opportunities remain linked to published scholarship records
            only. Recommendations, documents, and interview tools stay as entry
            points until their deeper slices are implemented.
          </p>
        </div>
        <div className="dashboard-hero__status">
          <StatusBadge label="Authenticated" variant="validated" />
          <StatusBadge
            label={state.profile ? "Profile on file" : "Profile pending"}
            variant={state.profile ? "validated" : "warning"}
          />
        </div>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="dashboard-error">
          <p className="section-eyebrow">Dashboard error</p>
          <h2 className="section-title">The workspace could not load cleanly.</h2>
          <p className="body-copy">{state.error}</p>
        </section>
      ) : null}

      <section className="dashboard-grid">
        <article className="surface-card" data-testid="profile-summary">
          <PageHeader
            eyebrow="Profile summary"
            title="Current student profile"
            description="A lightweight profile summary keeps the dashboard grounded in explicit inputs rather than generated assumptions."
          />
          {state.isLoading ? (
            <p className="body-copy">Loading saved workspace context.</p>
          ) : state.profile ? (
            <div className="surface-list">
              <article>
                <p className="list-heading">Target</p>
                <p className="body-copy">
                  {state.profile.target_degree_level} in {state.profile.target_field} for{" "}
                  {state.profile.target_country_code}
                </p>
              </article>
              <article>
                <p className="list-heading">Eligibility anchors</p>
                <p className="body-copy">
                  Citizenship {state.profile.citizenship_country_code}, GPA{" "}
                  {state.profile.gpa_value ?? "Not set"} / {state.profile.gpa_scale}
                </p>
              </article>
            </div>
          ) : (
            <div className="empty-panel">
              <p className="body-copy">
                No profile has been saved yet. Add your first profile to unlock
                profile-aware recommendation flows.
              </p>
              <Link className="auth-link auth-link--primary" href="/profile">
                Complete profile
              </Link>
            </div>
          )}
        </article>

        <article className="surface-panel" data-testid="saved-opportunities">
          <PageHeader
            eyebrow="Saved opportunities"
            title="Published scholarships you have saved"
            description="Saved opportunities are always tied to published scholarship records, never raw or review-state items."
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
                    <Link className="nav-link" href="/recommendations">
                      Recommendation entry
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
                No opportunities are saved yet. Use the published opportunities
                section below to add a short list.
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Core entry points"
          title="The dashboard links into the next MVP workflows."
          description="Each section below reserves a concrete next action without turning the workspace into an analytics-heavy control center."
        />
        <div className="dashboard-grid dashboard-grid--tight">
          <EntryCard
            href="/recommendations"
            label="Recommendations"
            description="Open the recommendation workspace once profile-aware ranking is ready."
          />
          <EntryCard
            href="/document-feedback"
            label="Document tools"
            description="Enter the bounded document-assistance flow with fact and guidance separation."
          />
          <EntryCard
            href="/interview"
            label="Interview practice"
            description="Open the text-first interview practice workflow."
          />
        </div>
      </section>

      <section className="surface-card" data-testid="published-opportunities">
        <PageHeader
          eyebrow="Published opportunities"
          title="Use published scholarships as the save source."
          description="This snapshot gives the dashboard a narrow, trustworthy save flow without adding a broader browse product prematurely."
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
              No published scholarships are currently available in the local
              data set. The save flow is ready once curation publishes records.
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
      <StatusBadge label="Workspace link" variant="planned" />
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
