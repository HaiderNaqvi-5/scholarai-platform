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
  RecommendationItem,
  RecommendationListResponse,
  SavedOpportunityItem,
  SavedOpportunityListResponse,
  StudentProfile,
} from "@/lib/types";

type RecommendationState = {
  isLoading: boolean;
  error: string | null;
  profile: StudentProfile | null;
  items: RecommendationItem[];
  savedItems: SavedOpportunityItem[];
};

export function RecommendationWorkspace() {
  const { accessToken } = useAuth();
  const [state, setState] = useState<RecommendationState>({
    isLoading: true,
    error: null,
    profile: null,
    items: [],
    savedItems: [],
  });

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadWorkspace = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const profile = await apiRequest<StudentProfile>("/profile", {
          token: accessToken,
        });
        const [recommendations, saved] = await Promise.all([
          apiRequest<RecommendationListResponse>("/recommendations", {
            method: "POST",
            token: accessToken,
            body: JSON.stringify({ limit: 8 }),
          }),
          apiRequest<SavedOpportunityListResponse>("/saved-opportunities", {
            token: accessToken,
          }),
        ]);

        if (!isActive) {
          return;
        }

        setState({
          isLoading: false,
          error: null,
          profile,
          items: recommendations.items,
          savedItems: saved.items,
        });
      } catch (caught) {
        if (!isActive) {
          return;
        }

        const error = caught as ApiError;
        setState({
          isLoading: false,
          error: error.message,
          profile: null,
          items: [],
          savedItems: [],
        });
      }
    };

    void loadWorkspace();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  const savedIds = useMemo(
    () => new Set(state.savedItems.map((item) => item.scholarship_id)),
    [state.savedItems],
  );

  const handleSave = async (scholarshipId: string) => {
    if (!accessToken) {
      return;
    }

    const item = await apiRequest<SavedOpportunityItem>(
      `/saved-opportunities/${scholarshipId}`,
      {
        method: "POST",
        token: accessToken,
      },
    );

    setState((current) => ({
      ...current,
      savedItems: [
        item,
        ...current.savedItems.filter(
          (savedItem) => savedItem.scholarship_id !== scholarshipId,
        ),
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
      savedItems: current.savedItems.filter(
        (item) => item.scholarship_id !== scholarshipId,
      ),
    }));
  };

  return (
    <AppShell
      eyebrow="Recommendations"
      title="Published scholarship recommendations now use a realistic demo dataset and clearer rationale."
      description="The recommendation list stays rules-first and deterministic. The UI highlights what matched, what limited fit, and why each record appeared in the shortlist."
    >
      <section className="recommendation-hero" data-testid="recommendations-workspace">
        <div className="dashboard-hero__intro">
          <p className="section-eyebrow">Demo quality pass</p>
          <h2 className="section-title">
            Recommendations remain grounded in published scholarship records only.
          </h2>
          <p className="body-copy">
            The seeded demo dataset includes published Canada-first opportunities,
            one Fulbright-related US example, and internal-only raw or validated
            records that stay out of the student flow.
          </p>
        </div>
        <div className="dashboard-hero__status">
          <StatusBadge label="Published only" variant="validated" />
          <StatusBadge label="Deterministic fit" variant="generated" />
        </div>
      </section>

      <section className="page-grid">
        <article className="data-callout">
          <p className="list-label">Validated facts</p>
          <p className="body-copy">
            Titles, providers, deadlines, target countries, and publication state
            come from curated records already marked published.
          </p>
        </article>
        <article className="guidance-callout">
          <p className="list-label">Generated explanation</p>
          <p className="body-copy">
            Match summaries and constraints are derived from explicit eligibility
            rules. They do not claim hidden model insight or scholarship-rule authority.
          </p>
        </article>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="recommendations-error">
          <PageHeader
            eyebrow="Recommendation state"
            title="Recommendations are not ready yet."
            description={state.error}
          />
          {!state.profile ? (
            <Link className="auth-link auth-link--primary" href="/profile">
              Complete profile first
            </Link>
          ) : null}
        </section>
      ) : null}

      <section className="surface-card">
        <PageHeader
          eyebrow="Profile anchor"
          title="Current recommendation input"
          description="This snapshot keeps the explanation traceable back to the exact profile values used by the deterministic filter."
        />
        {state.isLoading ? (
          <p className="body-copy">Loading your saved profile and seeded recommendation set.</p>
        ) : state.profile ? (
          <div className="surface-list">
            <article>
              <p className="list-heading">Target route</p>
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
          </div>
        ) : (
          <div className="empty-panel">
            <p className="body-copy">
              You need a saved profile before the recommendation engine can score published records.
            </p>
            <Link className="auth-link auth-link--primary" href="/profile">
              Add profile
            </Link>
          </div>
        )}
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Recommendation shortlist"
          title="The seeded shortlist explains both fit and caution."
          description="Strong matches surface first, but each card also tells you where the published record is broad, incomplete, or tighter than your profile."
        />
        {state.isLoading ? (
          <p className="body-copy">Ranking seeded published records.</p>
        ) : state.items.length > 0 ? (
          <div className="recommendation-list">
            {state.items.map((item) => {
              const isSaved = savedIds.has(item.scholarship_id);
              return (
                <article
                  className="recommendation-card"
                  data-testid="recommendation-card"
                  key={item.scholarship_id}
                >
                  <div className="recommendation-card__header">
                    <div className="meta-row">
                      <StatusBadge
                        label={`${Math.round(item.estimated_fit_score * 100)}% ${item.fit_band}`}
                        variant={fitVariant(item.fit_band)}
                      />
                      <StatusBadge label="Published source" variant="validated" />
                    </div>
                    <p className="route-card__label">
                      {item.country_code} ·{" "}
                      {item.deadline_at
                        ? `Deadline ${new Date(item.deadline_at).toLocaleDateString()}`
                        : "Deadline not listed"}
                    </p>
                  </div>

                  <div className="recommendation-card__body">
                    <div>
                      <h3 className="route-card__title">{item.title}</h3>
                      <p className="route-card__description">
                        {item.provider_name ?? "Provider not listed"}
                      </p>
                    </div>
                    <p className="recommendation-summary">{item.match_summary}</p>
                  </div>

                  <div className="recommendation-grid">
                    <section className="explanation-panel">
                      <p className="list-label">Criteria satisfied</p>
                      <ul className="detail-list">
                        {item.matched_criteria.map((criterion) => (
                          <li key={criterion}>{criterion}</li>
                        ))}
                      </ul>
                    </section>

                    <section className="explanation-panel explanation-panel--caution">
                      <p className="list-label">Ranking constraints</p>
                      {item.constraint_notes.length > 0 ? (
                        <ul className="detail-list">
                          {item.constraint_notes.map((note) => (
                            <li key={note}>{note}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="body-copy">
                          No material constraints surfaced from the published record.
                        </p>
                      )}
                    </section>
                  </div>

                  <div className="dashboard-actions">
                    <Link
                      className="nav-link"
                      href={`/scholarships/${item.scholarship_id}`}
                    >
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
                    <Link className="nav-link" href="/dashboard">
                      Open dashboard
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-panel">
            <p className="body-copy">
              No published seeded records matched your current profile. Adjust your target field, GPA, or country to see the available demo paths.
            </p>
            <Link className="auth-link auth-link--primary" href="/profile">
              Refine profile
            </Link>
          </div>
        )}
      </section>
    </AppShell>
  );
}

function fitVariant(
  fitBand: RecommendationItem["fit_band"],
): "validated" | "generated" | "warning" {
  if (fitBand === "strong") {
    return "validated";
  }
  if (fitBand === "possible") {
    return "generated";
  }
  return "warning";
}
