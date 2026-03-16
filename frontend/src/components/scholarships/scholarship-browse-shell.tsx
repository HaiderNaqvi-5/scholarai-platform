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
} from "@/lib/types";

const COUNTRY_FILTERS = [
  { label: "All published", value: "all" },
  { label: "Canada", value: "CA" },
  { label: "Fulbright scope", value: "US" },
] as const;

type CountryFilter = (typeof COUNTRY_FILTERS)[number]["value"];

type BrowseState = {
  isLoading: boolean;
  error: string | null;
  items: ScholarshipListItem[];
  appliedCountryCode: string | null;
  savedIds: Set<string>;
  isSaving: string | null;
};

export function ScholarshipBrowseShell() {
  const { accessToken, isAuthenticated } = useAuth();
  const [countryFilter, setCountryFilter] = useState<CountryFilter>("all");
  const [state, setState] = useState<BrowseState>({
    isLoading: true,
    error: null,
    items: [],
    appliedCountryCode: null,
    savedIds: new Set<string>(),
    isSaving: null,
  });

  useEffect(() => {
    let isActive = true;

    const loadData = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const query = new URLSearchParams({ limit: "24" });
        if (countryFilter !== "all") {
          query.set("country_code", countryFilter);
        }

        const scholarshipPromise = apiRequest<ScholarshipListResponse>(
          `/scholarships?${query.toString()}`,
        );
        const savedPromise = accessToken
          ? apiRequest<SavedOpportunityListResponse>("/saved-opportunities", {
              token: accessToken,
            })
          : Promise.resolve({ items: [] } satisfies SavedOpportunityListResponse);

        const [scholarships, saved] = await Promise.all([
          scholarshipPromise,
          savedPromise,
        ]);

        if (!isActive) {
          return;
        }

        setState({
          isLoading: false,
          error: null,
          items: scholarships.items,
          appliedCountryCode: scholarships.applied_country_code,
          savedIds: new Set(saved.items.map((item) => item.scholarship_id)),
          isSaving: null,
        });
      } catch (caught) {
        if (!isActive) {
          return;
        }

        const error = caught as ApiError;
        setState((current) => ({
          ...current,
          isLoading: false,
          error: error.message,
          items: [],
          appliedCountryCode: null,
          isSaving: null,
        }));
      }
    };

    void loadData();

    return () => {
      isActive = false;
    };
  }, [accessToken, countryFilter]);

  const heading = useMemo(() => {
    if (state.appliedCountryCode === "CA") {
      return "Published Canada-first opportunities";
    }
    if (state.appliedCountryCode === "US") {
      return "Published Fulbright-related US opportunities";
    }
    return "Published scholarship discovery";
  }, [state.appliedCountryCode]);

  const handleSaveToggle = async (scholarshipId: string, isSaved: boolean) => {
    if (!accessToken) {
      return;
    }

    setState((current) => ({ ...current, isSaving: scholarshipId, error: null }));

    try {
      if (isSaved) {
        await apiRequest<void>(`/saved-opportunities/${scholarshipId}`, {
          method: "DELETE",
          token: accessToken,
        });
        setState((current) => {
          const nextSavedIds = new Set(current.savedIds);
          nextSavedIds.delete(scholarshipId);
          return { ...current, savedIds: nextSavedIds, isSaving: null };
        });
        return;
      }

      const saved = await apiRequest<SavedOpportunityItem>(
        `/saved-opportunities/${scholarshipId}`,
        {
          method: "POST",
          token: accessToken,
        },
      );
      setState((current) => {
        const nextSavedIds = new Set(current.savedIds);
        nextSavedIds.add(saved.scholarship_id);
        return { ...current, savedIds: nextSavedIds, isSaving: null };
      });
    } catch (caught) {
      const error = caught as ApiError;
      setState((current) => ({ ...current, error: error.message, isSaving: null }));
    }
  };

  return (
    <AppShell
      eyebrow="Public discovery"
      title="Browse published scholarship records without stepping outside the curated MVP corpus."
      description="This view exposes only published opportunities, keeps Canada-first scope explicit, and ties deeper actions back into authenticated recommendation and save flows."
    >
      <section className="recommendation-hero" data-testid="scholarship-browse-shell">
        <div className="dashboard-hero__intro">
          <p className="section-eyebrow">Published scholarship corpus</p>
          <h2 className="section-title">{heading}</h2>
          <p className="body-copy">
            Raw and validated records stay inside curator tooling. This browse surface
            only exposes published records that remain in documented MVP scope.
          </p>
        </div>
        <div className="dashboard-hero__status">
          <StatusBadge label="Published only" variant="validated" />
          <StatusBadge label="Public read access" variant="generated" />
        </div>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Browse controls"
          title="Keep discovery narrow and explicit"
          description="The filter is intentionally small: published records only, with Canada-first scope and Fulbright-limited US access."
        />
        <div className="toggle-row">
          {COUNTRY_FILTERS.map((filter) => (
            <button
              className={
                countryFilter === filter.value
                  ? "toggle-chip toggle-chip--active"
                  : "toggle-chip"
              }
              key={filter.value}
              onClick={() => setCountryFilter(filter.value)}
              type="button"
            >
              {filter.label}
            </button>
          ))}
        </div>
      </section>

      {state.error ? (
        <section className="surface-card" data-testid="scholarship-browse-error">
          <p className="section-eyebrow">Scholarship browse error</p>
          <h2 className="section-title">The published scholarship view could not load.</h2>
          <p className="body-copy">{state.error}</p>
        </section>
      ) : null}

      <section className="surface-card">
        <PageHeader
          eyebrow="Published results"
          title="Use browse for public discovery, then move into saved and recommendation workflows."
          description="Cards stay concise: title, provider, deadline, scope, and a direct route into the scholarship detail view."
        />
        {state.isLoading ? (
          <p className="body-copy">Loading published scholarships.</p>
        ) : state.items.length > 0 ? (
          <div className="recommendation-list">
            {state.items.map((item) => {
              const isSaved = state.savedIds.has(item.scholarship_id);
              return (
                <article className="recommendation-card" key={item.scholarship_id}>
                  <div className="recommendation-card__header">
                    <div className="meta-row">
                      <StatusBadge label="Published" variant="validated" />
                      <span className="route-card__label">{item.country_code}</span>
                    </div>
                    <p className="route-card__label">
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
                    <p className="body-copy">
                      Open the full record to inspect scope, eligibility anchors, provenance,
                      and the published source link before saving or applying.
                    </p>
                  </div>
                  <div className="dashboard-actions">
                    <Link className="nav-link" href={`/scholarships/${item.scholarship_id}`}>
                      View details
                    </Link>
                    {isAuthenticated ? (
                      <button
                        className={
                          isSaved
                            ? "auth-link auth-link--secondary"
                            : "auth-link auth-link--primary"
                        }
                        disabled={state.isSaving === item.scholarship_id}
                        onClick={() =>
                          void handleSaveToggle(item.scholarship_id, isSaved)
                        }
                        type="button"
                      >
                        {state.isSaving === item.scholarship_id
                          ? "Updating"
                          : isSaved
                            ? "Saved"
                            : "Save opportunity"}
                      </button>
                    ) : (
                      <Link
                        className="auth-link auth-link--secondary"
                        href="/login?next=/scholarships"
                      >
                        Sign in to save
                      </Link>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-panel">
            <p className="body-copy">
              No published scholarships match the current scope filter. Try switching
              between Canada-first and Fulbright-limited US records.
            </p>
          </div>
        )}
      </section>
    </AppShell>
  );
}
