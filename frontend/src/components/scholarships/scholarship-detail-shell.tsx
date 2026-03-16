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
  ScholarshipDetail,
} from "@/lib/types";

type DetailState = {
  isLoading: boolean;
  error: string | null;
  item: ScholarshipDetail | null;
  isSaved: boolean;
  isSaving: boolean;
};

export function ScholarshipDetailShell({ scholarshipId }: { scholarshipId: string }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [state, setState] = useState<DetailState>({
    isLoading: true,
    error: null,
    item: null,
    isSaved: false,
    isSaving: false,
  });

  useEffect(() => {
    let isActive = true;

    const loadDetail = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const detailPromise = apiRequest<ScholarshipDetail>(`/scholarships/${scholarshipId}`);
        const savedPromise = accessToken
          ? apiRequest<SavedOpportunityListResponse>("/saved-opportunities", {
              token: accessToken,
            })
          : Promise.resolve({
              items: [],
              total: 0,
            } satisfies SavedOpportunityListResponse);

        const [detail, saved] = await Promise.all([detailPromise, savedPromise]);

        if (!isActive) {
          return;
        }

        setState({
          isLoading: false,
          error: null,
          item: detail,
          isSaved: saved.items.some((entry) => entry.scholarship_id === scholarshipId),
          isSaving: false,
        });
      } catch (caught) {
        if (!isActive) {
          return;
        }

        const error = caught as ApiError;
        setState({
          isLoading: false,
          error: error.message,
          item: null,
          isSaved: false,
          isSaving: false,
        });
      }
    };

    void loadDetail();

    return () => {
      isActive = false;
    };
  }, [accessToken, scholarshipId]);

  const handleSaveToggle = async () => {
    if (!accessToken || !state.item) {
      return;
    }

    setState((current) => ({ ...current, isSaving: true, error: null }));
    try {
      if (state.isSaved) {
        await apiRequest<void>(`/saved-opportunities/${scholarshipId}`, {
          method: "DELETE",
          token: accessToken,
        });
        setState((current) => ({ ...current, isSaved: false, isSaving: false }));
        return;
      }

      await apiRequest<SavedOpportunityItem>(`/saved-opportunities/${scholarshipId}`, {
        method: "POST",
        token: accessToken,
      });
      setState((current) => ({ ...current, isSaved: true, isSaving: false }));
    } catch (caught) {
      const error = caught as ApiError;
      setState((current) => ({ ...current, error: error.message, isSaving: false }));
    }
  };

  const detailFacts = useMemo(() => {
    if (!state.item) {
      return [];
    }

    return [
      { label: "Country", value: state.item.country_code },
      {
        label: "Deadline",
        value: state.item.deadline_at
          ? new Date(state.item.deadline_at).toLocaleDateString()
          : "Not listed",
      },
      {
        label: "Funding type",
        value: state.item.funding_type
          ? state.item.funding_type.replaceAll("_", " ")
          : "Not published",
      },
      {
        label: "Funding range",
        value:
          state.item.funding_amount_min !== null || state.item.funding_amount_max !== null
            ? `${state.item.funding_amount_min ?? state.item.funding_amount_max} - ${state.item.funding_amount_max ?? state.item.funding_amount_min}`
            : "Amount not published",
      },
      {
        label: "Last validated",
        value: state.item.last_validated_at
          ? new Date(state.item.last_validated_at).toLocaleDateString()
          : "Not recorded",
      },
      {
        label: "Source document",
        value: state.item.source_document_ref ?? "Not linked",
      },
    ];
  }, [state.item]);

  return (
    <AppShell
      eyebrow="Scholarship detail"
      title="Inspect a published scholarship record before you plan around it."
      description="The detail view keeps official scholarship facts primary and uses actions only as secondary support."
    >
      {state.error ? (
        <section className="surface-card" data-testid="scholarship-detail-error">
          <PageHeader
            eyebrow="Record status"
            title="The scholarship record could not be opened."
            description={state.error}
          />
          <Link className="nav-link" href="/scholarships">
            Return to scholarships
          </Link>
        </section>
      ) : null}

      {state.isLoading ? (
        <section className="surface-card">
          <p className="body-copy">Loading published scholarship details.</p>
        </section>
      ) : state.item ? (
        <>
          <section className="recommendation-hero" data-testid="scholarship-detail-shell">
            <div className="dashboard-hero__intro">
              <p className="section-eyebrow">Published scholarship</p>
              <h2 className="section-title">{state.item.title}</h2>
              <p className="body-copy">
                {state.item.provider_name ?? "Provider not listed"} · {state.item.country_code}
              </p>
            </div>
            <div className="dashboard-hero__status">
              <StatusBadge label="Published" variant="validated" />
              <StatusBadge label="Student-facing facts" variant="neutral" />
            </div>
          </section>

          <section className="detail-layout">
            <article className="surface-panel">
              <PageHeader
                eyebrow="Published summary"
                title="The scholarship context you can plan against"
                description="This column keeps the official summary, requirement language, and funding context together."
              />
              <div className="surface-list">
                <article>
                  <p className="list-heading">Summary</p>
                  <p className="body-copy">{state.item.summary ?? "No published summary yet."}</p>
                </article>
                <article>
                  <p className="list-heading">Funding summary</p>
                  <p className="body-copy">
                    {state.item.funding_summary ?? "Funding details were not published."}
                  </p>
                </article>
                <article>
                  <p className="list-heading">Requirement summary</p>
                  <ul className="detail-list">
                    {state.item.requirement_summary.map((entry) => (
                      <li key={entry}>{entry}</li>
                    ))}
                  </ul>
                </article>
                <article>
                  <p className="list-heading">Publication note</p>
                  <p className="body-copy">{state.item.publication_hint}</p>
                </article>
              </div>
            </article>

            <div className="collection-grid">
              <article className="surface-card">
                <PageHeader
                  eyebrow="Actions"
                  title="Move from reading to planning"
                  description="Saving remains optional and authenticated; the public record stays readable for anyone."
                />
                <div className="surface-list">
                  <article>
                    <p className="list-heading">Source link</p>
                    <a className="nav-link" href={state.item.source_url} rel="noreferrer" target="_blank">
                      Open published source
                    </a>
                  </article>
                  <article>
                    <p className="list-heading">Next step</p>
                    <div className="dashboard-actions">
                      {isAuthenticated ? (
                        <button
                          className={
                            state.isSaved
                              ? "auth-link auth-link--secondary"
                              : "auth-link auth-link--primary"
                          }
                          disabled={state.isSaving}
                          onClick={() => void handleSaveToggle()}
                          type="button"
                        >
                          {state.isSaving
                            ? "Updating"
                            : state.isSaved
                              ? "Saved"
                              : "Save opportunity"}
                        </button>
                      ) : (
                        <Link
                          className="auth-link auth-link--secondary"
                          href={`/login?next=/scholarships/${scholarshipId}`}
                        >
                          Sign in to save
                        </Link>
                      )}
                      <Link className="nav-link" href="/recommendations">
                        Open recommendations
                      </Link>
                    </div>
                  </article>
                </div>
              </article>

              <article className="surface-card">
                <PageHeader
                  eyebrow="Structured facts"
                  title="Key scholarship details"
                  description="These fields come from the published structured record rather than generated guidance."
                />
                <ul className="detail-list">
                  {detailFacts.map((fact) => (
                    <li key={fact.label}>
                      {fact.label}: {fact.value}
                    </li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          <section className="split-panel">
            <article className="data-callout">
              <p className="list-label">Eligibility anchors</p>
              <ul className="detail-list">
                <li>Degree levels: {state.item.degree_levels.join(", ") || "Not listed"}</li>
                <li>Field tags: {state.item.field_tags.join(", ") || "Not listed"}</li>
                <li>
                  Citizenship rules: {state.item.citizenship_rules.join(", ") || "Not specified"}
                </li>
                <li>
                  Minimum GPA:{" "}
                  {state.item.min_gpa_value !== null
                    ? state.item.min_gpa_value.toString()
                    : "No minimum published"}
                </li>
              </ul>
            </article>
            <article className="guidance-callout">
              <p className="list-label">Planning reminder</p>
              <p className="body-copy">
                Use this page for official scholarship information. Recommendation fit and
                preparation guidance should be treated as advisory layers on top of it.
              </p>
            </article>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
