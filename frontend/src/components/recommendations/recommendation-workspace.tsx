"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { ShapWaterfallChart } from "@/components/recommendations/shap-waterfall-chart";
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
    if (!accessToken) return;

    let isActive = true;

    const loadWorkspace = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const profile = await apiRequest<StudentProfile>("/profiles", {
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

        if (!isActive) return;

        setState({
          isLoading: false,
          error: null,
          profile,
          items: recommendations.items,
          savedItems: saved.items,
        });
      } catch (caught) {
        if (!isActive) return;
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
    if (!accessToken) return;

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
    if (!accessToken) return;

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
      title="Scholarships ranked by your profile."
      description="Each recommendation explains why a scholarship fits and what to verify."
      intro={
        <div className="meta-row">
          <StatusBadge label="Published records" variant="validated" />
          <StatusBadge label="Profile-based ranking" variant="generated" />
        </div>
      }
    >
      <section className="workspace-layout" data-testid="recommendations-workspace">
        <div className="collection-grid">
          {state.error ? (
            <section className="surface-card" data-testid="recommendations-error">
              <PageHeader
                eyebrow="Status"
                title="Recommendations are not available."
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
              title="Your matches"
              description="Strong matches appear first. Each card shows what aligned and what needs verification."
            />
            {state.isLoading ? (
              <div className="collection-grid">
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
              </div>
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
                          <span className="route-card__label">{item.country_code}</span>
                        </div>
                        <p className="route-card__label">
                          {item.deadline_at
                            ? `Deadline ${new Date(item.deadline_at).toLocaleDateString()}`
                            : "No deadline listed"}
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
                        {item.rationale?.summary ? (
                          <p className="body-copy">{item.rationale.summary}</p>
                        ) : null}
                      </div>

                      <div className="recommendation-grid">
                        <section className="explanation-panel">
                          <p className="list-label">
                            {item.signal_language?.facts_label ?? "What aligned"}
                          </p>
                          <ul className="detail-list">
                            {(item.rationale?.facts ?? []).length > 0
                              ? item.rationale?.facts.map((factor) => (
                                  <li key={`${item.scholarship_id}-${factor.code}`}>
                                    <strong>{factor.label}:</strong> {factor.detail}
                                  </li>
                                ))
                              : item.matched_criteria.map((criterion) => (
                                  <li key={criterion}>{criterion}</li>
                                ))}
                          </ul>
                        </section>

                        <section className="explanation-panel explanation-panel--caution">
                          <p className="list-label">
                            {item.signal_language?.estimated_signals_label ??
                              "Estimated ranking signals"}
                          </p>
                          {(item.rationale?.estimated_signals ?? []).length > 0 ? (
                            <ul className="detail-list">
                              {item.rationale?.estimated_signals.map((factor) => (
                                <li key={`${item.scholarship_id}-signal-${factor.code}`}>
                                  <strong>{factor.label}:</strong> {factor.detail}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="body-copy">
                              Semantic ranking signals were not available for this item.
                            </p>
                          )}
                          {item.signal_language?.estimated_signals_notice ? (
                            <p className="body-copy">{item.signal_language.estimated_signals_notice}</p>
                          ) : null}
                          <p className="list-label">What to verify</p>
                          {item.constraint_notes.length > 0 ? (
                            <ul className="detail-list">
                              {item.constraint_notes.map((note) => (
                                <li key={`${item.scholarship_id}-constraint-${note}`}>{note}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="body-copy">
                              No cautions found in the current record.
                            </p>
                          )}
                          {item.fallback_reason ? (
                            <p className="body-copy">{item.fallback_reason}</p>
                          ) : null}
                        </section>
                      </div>

                      <div className="recommendation-grid">
                        <section className="explanation-panel">
                          <p className="list-label">Stage status</p>
                          <ul className="detail-list">
                            {item.rationale ? (
                              <>
                                <li>Scope: {item.rationale.stages.scope.status}</li>
                                <li>Eligibility: {item.rationale.stages.eligibility.status}</li>
                                <li>Retrieval: {item.rationale.stages.retrieval.status}</li>
                                <li>Rerank: {item.rationale.stages.rerank.status}</li>
                              </>
                            ) : (
                              <li>Stage details are not available for this item.</li>
                            )}
                          </ul>
                        </section>

                        <section className="explanation-panel">
                          <p className="list-label">Ranking features</p>
                          <ul className="detail-list">
                            {item.heuristic_factors ? (
                              Object.entries(item.heuristic_factors).map(([key, value]) => (
                                <li key={`${item.scholarship_id}-feature-${key}`}>
                                  {key.replace(/_/g, " ")}: {value.toFixed(3)}
                                </li>
                              ))
                            ) : (
                              <li>Feature-level ranking details are not available.</li>
                            )}
                          </ul>
                        </section>
                      </div>

                      {item.shap_explanation && (
                        <ShapWaterfallChart
                          shapExplanation={item.shap_explanation}
                        />
                      )}

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
                          {isSaved ? "Saved" : "Save"}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                title="No recommendations found"
                description="Adjust your target field, GPA, or country to broaden results."
                action={
                  <Link className="auth-link auth-link--primary" href="/profile">
                    Edit profile
                  </Link>
                }
              />
            )}
          </section>
        </div>

        <div className="collection-grid">
          <section className="surface-panel">
            <PageHeader
              eyebrow="Profile"
              title="Your ranking inputs"
              description="Recommendations are based on these profile fields."
            />
            {state.isLoading ? (
              <div className="surface-list">
                <SkeletonLine count={3} />
                <SkeletonLine count={2} />
              </div>
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
                </div>
              </div>
            ) : (
              <EmptyState
                title="Profile incomplete"
                description="Create a profile to generate your first recommendations."
                action={
                  <Link className="auth-link auth-link--primary" href="/profile">
                    Add profile
                  </Link>
                }
              />
            )}
          </section>

          <section className="surface-card">
            <PageHeader
              eyebrow="How it works"
              title="About these recommendations"
              description="Rankings explain why a scholarship surfaced — they don't predict outcomes."
            />
            <div className="split-panel">
              <article className="data-callout">
                <p className="list-heading">Verified facts</p>
                <p className="body-copy">
                  Titles, providers, and deadlines come from published records.
                </p>
              </article>
              <article className="guidance-callout">
                <p className="list-heading">Generated explanations</p>
                <p className="body-copy">
                  Fit scores and reasoning summarize your profile against scholarship criteria. They are advisory.
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
  if (fitBand === "strong") return "validated";
  if (fitBand === "possible") return "generated";
  return "warning";
}
