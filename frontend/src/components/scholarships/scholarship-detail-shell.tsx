"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { ErrorState, FeedbackNotice } from "@/components/ui/feedback-state";
import { SkeletonLine } from "@/components/ui/skeleton";
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
  notice: string | null;
};

export function ScholarshipDetailShell({ scholarshipId }: { scholarshipId: string }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [state, setState] = useState<DetailState>({
    isLoading: true,
    error: null,
    item: null,
    isSaved: false,
    isSaving: false,
    notice: null,
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

        if (!isActive) return;

        setState({
          isLoading: false,
          error: null,
          item: detail,
          isSaved: saved.items.some((entry) => entry.scholarship_id === scholarshipId),
          isSaving: false,
          notice: null,
        });
      } catch (caught) {
        if (!isActive) return;
        const error = caught as ApiError;
        setState({
          isLoading: false,
          error: error.message,
          item: null,
          isSaved: false,
          isSaving: false,
          notice: null,
        });
      }
    };

    void loadDetail();

    return () => {
      isActive = false;
    };
  }, [accessToken, scholarshipId]);

  const handleSaveToggle = async () => {
    if (!accessToken || !state.item) return;

    setState((current) => ({
      ...current,
      isSaving: true,
      error: null,
      notice: null,
    }));
    try {
      if (state.isSaved) {
        await apiRequest<void>(`/saved-opportunities/${scholarshipId}`, {
          method: "DELETE",
          token: accessToken,
        });
        setState((current) => ({
          ...current,
          isSaved: false,
          isSaving: false,
          notice: "Removed from your shortlist.",
        }));
        return;
      }

      await apiRequest<SavedOpportunityItem>(`/saved-opportunities/${scholarshipId}`, {
        method: "POST",
        token: accessToken,
      });
      setState((current) => ({
        ...current,
        isSaved: true,
        isSaving: false,
        notice: "Saved to your shortlist.",
      }));
    } catch (caught) {
      const error = caught as ApiError;
      setState((current) => ({ ...current, error: error.message, isSaving: false }));
    }
  };

  const detailFacts = useMemo(() => {
    if (!state.item) return [];

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
            ? `$${state.item.funding_amount_min ?? state.item.funding_amount_max} – $${state.item.funding_amount_max ?? state.item.funding_amount_min}`
            : "Not published",
      },
      {
        label: "Last validated",
        value: state.item.last_validated_at
          ? new Date(state.item.last_validated_at).toLocaleDateString()
          : "Not recorded",
      },
      {
        label: "Source",
        value: state.item.source_document_ref ?? "Not linked",
      },
    ];
  }, [state.item]);

  return (
    <AppShell
      eyebrow="Scholarship detail"
      title="Review this scholarship before planning around it."
      description="Official facts from the published record. Actions are secondary."
    >
      {state.error ? (
        <ErrorState
          testId="scholarship-detail-error"
          title="Could not load this scholarship."
          description={state.error}
          action={
            <Link className="nav-link" href="/scholarships">
              Back to scholarships
            </Link>
          }
        />
      ) : null}

      {state.isLoading ? (
        <section className="surface-card">
          <SkeletonLine count={2} />
          <br />
          <SkeletonLine count={4} />
        </section>
      ) : state.item ? (
        <>
          <section
            className="recommendation-hero"
            data-testid="scholarship-detail-shell"
            aria-busy={state.isSaving}
          >
            <div className="dashboard-hero__intro">
              <h2 className="section-title">{state.item.title}</h2>
              <p className="body-copy">
                {state.item.provider_name ?? "Provider not listed"} · {state.item.country_code}
              </p>
            </div>
            <div className="meta-row">
              <StatusBadge label="Published" variant="validated" />
              {state.item.deadline_at ? (
                <span className="route-card__label">
                  Deadline {new Date(state.item.deadline_at).toLocaleDateString()}
                </span>
              ) : null}
            </div>
          </section>

          <section className="detail-layout">
            <article className="surface-panel">
              <PageHeader
                eyebrow="Summary"
                title="Scholarship details"
                description="Official information from the published record."
              />
              <div className="surface-list">
                <article>
                  <p className="list-heading">Description</p>
                  <p className="body-copy">{state.item.summary ?? "No summary published."}</p>
                </article>
                <article>
                  <p className="list-heading">Funding</p>
                  <p className="body-copy">
                    {state.item.funding_summary ?? "Funding details not published."}
                  </p>
                </article>
                <article>
                  <p className="list-heading">Requirements</p>
                  <ul className="detail-list">
                    {state.item.requirement_summary.map((entry) => (
                      <li key={entry}>{entry}</li>
                    ))}
                  </ul>
                </article>
                {state.item.publication_hint ? (
                  <article>
                    <p className="list-heading">Note</p>
                    <p className="body-copy">{state.item.publication_hint}</p>
                  </article>
                ) : null}
              </div>
            </article>

            <div className="collection-grid">
              <article className="surface-card">
                <PageHeader
                  eyebrow="Key facts"
                  title="Structured data"
                  description="Verified fields from the published record."
                />
                <div className="surface-list">
                  {detailFacts.map((fact) => (
                    <article key={fact.label}>
                      <p className="route-card__label">{fact.label}</p>
                      <p className="body-copy">{fact.value}</p>
                    </article>
                  ))}
                </div>
              </article>

              <article className="surface-card">
                <PageHeader
                  eyebrow="Eligibility"
                  title="Requirements"
                  description="Official eligibility criteria from the scholarship provider."
                />
                <div className="surface-list">
                  <article>
                    <p className="route-card__label">Degree levels</p>
                    <p className="body-copy">{state.item.degree_levels.join(", ") || "Not listed"}</p>
                  </article>
                  <article>
                    <p className="route-card__label">Fields</p>
                    <p className="body-copy">{state.item.field_tags.join(", ") || "Not listed"}</p>
                  </article>
                  <article>
                    <p className="route-card__label">Citizenship</p>
                    <p className="body-copy">{state.item.citizenship_rules.join(", ") || "Not specified"}</p>
                  </article>
                  <article>
                    <p className="route-card__label">Minimum GPA</p>
                    <p className="body-copy">
                      {state.item.min_gpa_value !== null
                        ? state.item.min_gpa_value.toString()
                        : "None published"}
                    </p>
                  </article>
                </div>
              </article>

              <article className="surface-card">
                {state.notice ? (
                  <div aria-live="polite">
                    <FeedbackNotice message={state.notice} variant="success" />
                  </div>
                ) : null}
                <div className="dashboard-actions">
                  <a
                    className="nav-link"
                    href={state.item.source_url}
                    rel="noreferrer"
                    target="_blank"
                    aria-label="View original scholarship source (opens in a new tab)"
                  >
                    View original source
                  </a>
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
                      aria-pressed={state.isSaved}
                      aria-label={state.isSaved ? "Remove from shortlist" : "Save to shortlist"}
                    >
                      {state.isSaving
                        ? "Updating…"
                        : state.isSaved
                          ? "Saved"
                          : "Save to shortlist"}
                    </button>
                  ) : (
                    <Link
                      className="auth-link auth-link--secondary"
                      href={`/login?next=/scholarships/${scholarshipId}`}
                    >
                      Sign in to save
                    </Link>
                  )}
                </div>
              </article>
            </div>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
