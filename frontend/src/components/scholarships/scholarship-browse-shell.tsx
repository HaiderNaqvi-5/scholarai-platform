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

const FIELD_FILTERS = [
  { label: "All fields", value: "all" },
  { label: "Data Science", value: "data science" },
  { label: "Artificial Intelligence", value: "artificial intelligence" },
  { label: "Analytics", value: "analytics" },
] as const;

const DEADLINE_FILTERS = [
  { label: "Any deadline", value: "all" },
  { label: "30 days", value: "30" },
  { label: "60 days", value: "60" },
  { label: "90 days", value: "90" },
] as const;

const SORT_OPTIONS = [
  { label: "Nearest deadline", value: "deadline" },
  { label: "Alphabetical", value: "title" },
  { label: "Recently added", value: "recent" },
] as const;

type CountryFilter = (typeof COUNTRY_FILTERS)[number]["value"];
type FieldFilter = (typeof FIELD_FILTERS)[number]["value"];
type DeadlineFilter = (typeof DEADLINE_FILTERS)[number]["value"];
type SortFilter = (typeof SORT_OPTIONS)[number]["value"];

type BrowseState = {
  isLoading: boolean;
  error: string | null;
  items: ScholarshipListItem[];
  appliedCountryCode: string | null;
  appliedQuery: string | null;
  appliedFieldTag: string | null;
  appliedDegreeLevel: string | null;
  appliedDeadlineWithinDays: number | null;
  appliedSort: SortFilter;
  savedIds: Set<string>;
  isSaving: string | null;
};

export function ScholarshipBrowseShell() {
  const { accessToken, isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [countryFilter, setCountryFilter] = useState<CountryFilter>("all");
  const [fieldFilter, setFieldFilter] = useState<FieldFilter>("all");
  const [deadlineFilter, setDeadlineFilter] = useState<DeadlineFilter>("all");
  const [sortFilter, setSortFilter] = useState<SortFilter>("deadline");
  const [state, setState] = useState<BrowseState>({
    isLoading: true,
    error: null,
    items: [],
    appliedCountryCode: null,
    appliedQuery: null,
    appliedFieldTag: null,
    appliedDegreeLevel: null,
    appliedDeadlineWithinDays: null,
    appliedSort: "deadline",
    savedIds: new Set<string>(),
    isSaving: null,
  });

  useEffect(() => {
    let isActive = true;

    const loadData = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const query = new URLSearchParams({
          limit: "24",
          degree_level: "MS",
          sort: sortFilter,
        });
        if (countryFilter !== "all") {
          query.set("country_code", countryFilter);
        }
        if (fieldFilter !== "all") {
          query.set("field_tag", fieldFilter);
        }
        if (deadlineFilter !== "all") {
          query.set("deadline_within_days", deadlineFilter);
        }
        if (searchQuery.trim()) {
          query.set("query", searchQuery.trim());
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
          appliedQuery: scholarships.applied_query,
          appliedFieldTag: scholarships.applied_field_tag,
          appliedDegreeLevel: scholarships.applied_degree_level,
          appliedDeadlineWithinDays: scholarships.applied_deadline_within_days,
          appliedSort: scholarships.applied_sort,
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
          isSaving: null,
        }));
      }
    };

    void loadData();

    return () => {
      isActive = false;
    };
  }, [accessToken, countryFilter, deadlineFilter, fieldFilter, searchQuery, sortFilter]);

  const heading = useMemo(() => {
    if (state.appliedCountryCode === "CA") {
      return "Published Canada-first opportunities";
    }
    if (state.appliedCountryCode === "US") {
      return "Published Fulbright-related US opportunities";
    }
    return "Published scholarship discovery";
  }, [state.appliedCountryCode]);

  const appliedFilterPills = useMemo(() => {
    return [
      state.appliedDegreeLevel ? `Degree ${state.appliedDegreeLevel}` : null,
      state.appliedFieldTag ? `Field ${state.appliedFieldTag}` : null,
      state.appliedDeadlineWithinDays
        ? `Deadline within ${state.appliedDeadlineWithinDays} days`
        : null,
      state.appliedQuery ? `Search ${state.appliedQuery}` : null,
      `Sort ${state.appliedSort}`,
    ].filter(Boolean) as string[];
  }, [
    state.appliedDeadlineWithinDays,
    state.appliedDegreeLevel,
    state.appliedFieldTag,
    state.appliedQuery,
    state.appliedSort,
  ]);

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
      title="Browse the published scholarship corpus with the same scope discipline the MVP uses everywhere else."
      description="This view stays published-only, Canada-first, and explicit about filters, deadlines, and field alignment instead of pretending discovery is broader than the validated corpus."
    >
      <section className="recommendation-hero" data-testid="scholarship-browse-shell">
        <div className="dashboard-hero__intro">
          <p className="section-eyebrow">Published scholarship corpus</p>
          <h2 className="section-title">{heading}</h2>
          <p className="body-copy">
            Raw and validated records remain internal. This discovery surface only
            exposes published scholarship records that stay inside documented MVP scope.
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
          title="Search and filter the narrow published corpus"
          description="Filters stay intentionally practical: country, field family, deadline urgency, and a simple sort order."
        />
        <div className="form-grid">
          <label className="form-field">
            <span className="form-field__label">Search title or provider</span>
            <input
              className="text-input"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Waterloo, Fulbright, analytics"
              value={searchQuery}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Deadline window</span>
            <select
              className="text-input"
              onChange={(event) => setDeadlineFilter(event.target.value as DeadlineFilter)}
              value={deadlineFilter}
            >
              {DEADLINE_FILTERS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span className="form-field__label">Sort order</span>
            <select
              className="text-input"
              onChange={(event) => setSortFilter(event.target.value as SortFilter)}
              value={sortFilter}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
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
        <div className="toggle-row">
          {FIELD_FILTERS.map((filter) => (
            <button
              className={
                fieldFilter === filter.value
                  ? "toggle-chip toggle-chip--active"
                  : "toggle-chip"
              }
              key={filter.value}
              onClick={() => setFieldFilter(filter.value)}
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
          eyebrow="Applied filters"
          title="Keep the current discovery state explicit"
          description="The browse layer should make it obvious why a result set is narrow instead of making the corpus look larger than it is."
        />
        <div className="meta-row">
          {appliedFilterPills.map((pill) => (
            <StatusBadge key={pill} label={pill} variant="generated" />
          ))}
        </div>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="Published results"
          title="Use browse for public discovery, then move into saved and recommendation workflows."
          description="Cards stay concise but now surface field alignment and deadline urgency more clearly for demo-quality browsing."
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
                      Open the full record to inspect eligibility anchors, provenance,
                      and the published source link before saving or planning around it.
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
              No published scholarships match the current discovery settings. Try
              broadening the field filter, clearing the search text, or widening the
              deadline window.
            </p>
          </div>
        )}
      </section>
    </AppShell>
  );
}
