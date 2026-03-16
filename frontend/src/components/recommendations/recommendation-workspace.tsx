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
      title="Use a saved profile to review a shortlist that explains both fit and caution."
      description="Recommendations stay rules-first and tied to published scholarship records so the shortlist reads as guidance, not prediction."
      intro={
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="Published records only" variant="validated" />
            <StatusBadge label="Deterministic fit bands" variant="generated" />
          </div>
          <p className="body-copy">
            Match summaries reflect explicit profile fields and scholarship constraints.
            They are advisory, not authoritative scholarship decisions.
          </p>
        </div>
      }
    >
      <section className="workspace-layout" data-testid="recommendations-workspace">
        <div className="collection-grid">
          {state.error ? (
            <section className="surface-card" data-testid="recommendations-error">
              <PageHeader
                eyebrow="Recommendation status"
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
              eyebrow="Shortlist"
              title="Each recommendation keeps the reason visible"
              description="Strong matches surface first, but the interface also shows what may limit fit so the ranking stays honest."
            />
            {state.isLoading ? (
              <p className="body-copy">Loading your profile and shortlist.</p>
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
                          <p className="list-label">What aligned</p>
                          <ul className="detail-list">
                            {item.matched_criteria.map((criterion) => (
                              <li key={criterion}>{criterion}</li>
                            ))}
                          </ul>
                        </section>

                        <section className="explanation-panel explanation-panel--caution">
                          <p className="list-label">What to verify</p>
                          {item.constraint_notes.length > 0 ? (
                            <ul className="detail-list">
                              {item.constraint_notes.map((note) => (
                                <li key={note}>{note}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="body-copy">
                              No material cautions surfaced from the current published record.
                            </p>
                          )}
                        </section>
                      </div>

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
                  No published seeded records matched your current profile. Adjust your
                  target field, GPA, or country to broaden the shortlist.
                </p>
                <Link className="auth-link auth-link--primary" href="/profile">
                  Refine profile
                </Link>
              </div>
            )}
          </section>
        </div>

        <div className="collection-grid">
          <section className="surface-panel">
            <PageHeader
              eyebrow="Profile anchor"
              title="The input behind this shortlist"
              description="The recommendation path stays understandable because it is tied to explicit profile data."
            />
            {state.isLoading ? (
              <p className="body-copy">Loading profile context.</p>
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
                <div className="dashboard-actions">
                  <Link className="nav-link" href="/profile">
                    Edit profile
                  </Link>
                </div>
              </div>
            ) : (
              <div className="empty-panel">
                <p className="body-copy">
                  A saved profile is required before ScholarAI can score published records.
                </p>
                <Link className="auth-link auth-link--primary" href="/profile">
                  Add profile
                </Link>
              </div>
            )}
          </section>

          <section className="surface-card">
            <PageHeader
              eyebrow="Trust boundary"
              title="What this ranking means"
              description="The shortlist explains why a scholarship surfaced without pretending to be a scholarship outcome predictor."
            />
            <div className="surface-list">
              <article className="data-callout">
                <p className="list-heading">Validated facts</p>
                <p className="body-copy">
                  Titles, providers, deadlines, and publication state come directly from curated records.
                </p>
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Generated explanation</p>
                <p className="body-copy">
                  Fit bands and reasoning summarize explicit rules and profile inputs. They do
                  not replace the scholarship record itself.
                </p>
              </article>
            </div>
          </section>
        </div>
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
