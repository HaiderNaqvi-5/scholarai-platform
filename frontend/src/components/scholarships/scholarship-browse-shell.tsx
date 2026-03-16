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
  ScholarshipAppliedFilters,
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

const DEADLINE_WINDOWS = [
  { label: "Any deadline", value: "all" },
  { label: "30 days", value: "30" },
  { label: "60 days", value: "60" },
  { label: "90 days", value: "90" },
] as const;

const DEADLINE_AVAILABILITY = [
  { label: "Any availability", value: "all" },
  { label: "Has deadline", value: "true" },
  { label: "No deadline", value: "false" },
] as const;

const FUNDING_TYPES = [
  { label: "Any funding type", value: "all" },
  { label: "Tuition award", value: "tuition_award" },
  { label: "Stipend", value: "stipend" },
  { label: "Fellowship", value: "fellowship" },
  { label: "Comprehensive award", value: "comprehensive_award" },
  { label: "Bursary", value: "bursary" },
] as const;

const SORT_OPTIONS = [
  { label: "Nearest deadline", value: "deadline" },
  { label: "Alphabetical", value: "title" },
  { label: "Recently added", value: "recent" },
] as const;

type CountryFilter = (typeof COUNTRY_FILTERS)[number]["value"];
type FieldFilter = (typeof FIELD_FILTERS)[number]["value"];
type DeadlineWindow = (typeof DEADLINE_WINDOWS)[number]["value"];
type DeadlineAvailability = (typeof DEADLINE_AVAILABILITY)[number]["value"];
type FundingTypeFilter = (typeof FUNDING_TYPES)[number]["value"];
type SortFilter = (typeof SORT_OPTIONS)[number]["value"];

type BrowseState = {
  isLoading: boolean;
  error: string | null;
  items: ScholarshipListItem[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  appliedFilters: ScholarshipAppliedFilters;
  savedIds: Set<string>;
  isSaving: string | null;
};

const DEFAULT_PAGE_SIZE = 12;

export function ScholarshipBrowseShell() {
  const { accessToken, isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [countryFilter, setCountryFilter] = useState<CountryFilter>("all");
  const [fieldFilter, setFieldFilter] = useState<FieldFilter>("all");
  const [providerFilter, setProviderFilter] = useState("");
  const [fundingFilter, setFundingFilter] = useState<FundingTypeFilter>("all");
  const [deadlineWindow, setDeadlineWindow] = useState<DeadlineWindow>("all");
  const [deadlineAvailability, setDeadlineAvailability] =
    useState<DeadlineAvailability>("all");
  const [sortFilter, setSortFilter] = useState<SortFilter>("deadline");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [page, setPage] = useState(1);
  const [state, setState] = useState<BrowseState>({
    isLoading: true,
    error: null,
    items: [],
    total: 0,
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    hasMore: false,
    appliedFilters: {
      country_code: null,
      query: null,
      field_tag: null,
      degree_level: null,
      provider: null,
      funding_type: null,
      min_amount: null,
      max_amount: null,
      has_deadline: null,
      deadline_within_days: null,
      deadline_after: null,
      deadline_before: null,
      sort: "deadline",
    },
    savedIds: new Set<string>(),
    isSaving: null,
  });

  const updateSearchQuery = (value: string) => {
    setSearchQuery(value);
    setPage(1);
  };

  const updateCountryFilter = (value: CountryFilter) => {
    setCountryFilter(value);
    setPage(1);
  };

  const updateFieldFilter = (value: FieldFilter) => {
    setFieldFilter(value);
    setPage(1);
  };

  const updateProviderFilter = (value: string) => {
    setProviderFilter(value);
    setPage(1);
  };

  const updateFundingFilter = (value: FundingTypeFilter) => {
    setFundingFilter(value);
    setPage(1);
  };

  const updateDeadlineWindow = (value: DeadlineWindow) => {
    setDeadlineWindow(value);
    setPage(1);
  };

  const updateDeadlineAvailability = (value: DeadlineAvailability) => {
    setDeadlineAvailability(value);
    setPage(1);
  };

  const updateSortFilter = (value: SortFilter) => {
    setSortFilter(value);
    setPage(1);
  };

  const updateMinAmount = (value: string) => {
    setMinAmount(value);
    setPage(1);
  };

  const updateMaxAmount = (value: string) => {
    setMaxAmount(value);
    setPage(1);
  };

  useEffect(() => {
    let isActive = true;

    const loadData = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const query = new URLSearchParams({
          degree_level: "MS",
          sort: sortFilter,
          page: page.toString(),
          page_size: DEFAULT_PAGE_SIZE.toString(),
        });

        if (countryFilter !== "all") {
          query.set("country_code", countryFilter);
        }
        if (fieldFilter !== "all") {
          query.set("field_tag", fieldFilter);
        }
        if (providerFilter.trim()) {
          query.set("provider", providerFilter.trim());
        }
        if (fundingFilter !== "all") {
          query.set("funding_type", fundingFilter);
        }
        if (deadlineWindow !== "all") {
          query.set("deadline_within_days", deadlineWindow);
        }
        if (deadlineAvailability !== "all") {
          query.set("has_deadline", deadlineAvailability);
        }
        if (searchQuery.trim()) {
          query.set("query", searchQuery.trim());
        }
        if (minAmount.trim()) {
          query.set("min_amount", minAmount.trim());
        }
        if (maxAmount.trim()) {
          query.set("max_amount", maxAmount.trim());
        }

        const scholarshipPromise = apiRequest<ScholarshipListResponse>(
          `/scholarships?${query.toString()}`,
        );
        const savedPromise = accessToken
          ? apiRequest<SavedOpportunityListResponse>("/saved-opportunities", {
              token: accessToken,
            })
          : Promise.resolve({
              items: [],
              total: 0,
            } satisfies SavedOpportunityListResponse);

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
          total: scholarships.total,
          page: scholarships.page,
          pageSize: scholarships.page_size,
          hasMore: scholarships.has_more,
          appliedFilters: scholarships.applied_filters,
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
          total: 0,
          hasMore: false,
          isSaving: null,
        }));
      }
    };

    void loadData();

    return () => {
      isActive = false;
    };
  }, [
    accessToken,
    countryFilter,
    deadlineAvailability,
    deadlineWindow,
    fieldFilter,
    fundingFilter,
    maxAmount,
    minAmount,
    page,
    providerFilter,
    searchQuery,
    sortFilter,
  ]);

  const appliedFilterPills = useMemo(() => {
    const filters = state.appliedFilters;
    return [
      filters.country_code ? `Country ${filters.country_code}` : null,
      filters.degree_level ? `Degree ${filters.degree_level}` : null,
      filters.field_tag ? `Field ${filters.field_tag}` : null,
      filters.provider ? `Provider ${filters.provider}` : null,
      filters.funding_type ? `Funding ${filters.funding_type.replaceAll("_", " ")}` : null,
      filters.min_amount !== null ? `Min ${filters.min_amount}` : null,
      filters.max_amount !== null ? `Max ${filters.max_amount}` : null,
      filters.has_deadline === true
        ? "Has deadline"
        : filters.has_deadline === false
          ? "No deadline"
          : null,
      filters.deadline_within_days
        ? `Deadline within ${filters.deadline_within_days} days`
        : null,
    ].filter(Boolean) as string[];
  }, [state.appliedFilters]);

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

  const clearAllFilters = () => {
    setSearchQuery("");
    setCountryFilter("all");
    setFieldFilter("all");
    setProviderFilter("");
    setFundingFilter("all");
    setDeadlineWindow("all");
    setDeadlineAvailability("all");
    setSortFilter("deadline");
    setMinAmount("");
    setMaxAmount("");
    setPage(1);
  };

  return (
    <AppShell
      eyebrow="Scholarship discovery"
      title="Browse a published scholarship catalog with clear scope and visible filters."
      description="The discovery view stays disciplined: Canada-first, published-only, and explicit about the narrow MVP corpus."
      intro={
        <div className="surface-band">
          <div className="button-row">
            <StatusBadge label="Public catalog" variant="validated" />
            <StatusBadge label={`${state.total} visible records`} variant="neutral" />
          </div>
          <p className="body-copy">
            Students only see published records here. Internal raw and validated
            records remain inside the curation workflow.
          </p>
        </div>
      }
    >
      <section className="workspace-layout" data-testid="scholarship-browse-shell">
        <article className="surface-panel scholarship-filter-rail">
          <PageHeader
            eyebrow="Filter rail"
            title="Keep the search state visible"
            description="Filtering stays on the page so the catalog feels trustworthy and easy to adjust."
          />
          <div className="form-grid">
            <label className="form-field">
              <span className="form-field__label">Search title or provider</span>
              <input
                className="text-input"
                data-testid="scholarship-search-input"
                onChange={(event) => updateSearchQuery(event.target.value)}
                placeholder="Waterloo, Fulbright, analytics"
                value={searchQuery}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Provider</span>
              <input
                className="text-input"
                data-testid="scholarship-provider-input"
                onChange={(event) => updateProviderFilter(event.target.value)}
                placeholder="University of Waterloo"
                value={providerFilter}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Funding type</span>
              <select
                className="text-input"
                data-testid="scholarship-funding-select"
                onChange={(event) =>
                  updateFundingFilter(event.target.value as FundingTypeFilter)
                }
                value={fundingFilter}
              >
                {FUNDING_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span className="form-field__label">Deadline window</span>
              <select
                className="text-input"
                onChange={(event) =>
                  updateDeadlineWindow(event.target.value as DeadlineWindow)
                }
                value={deadlineWindow}
              >
                {DEADLINE_WINDOWS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span className="form-field__label">Deadline availability</span>
              <select
                className="text-input"
                onChange={(event) =>
                  updateDeadlineAvailability(
                    event.target.value as DeadlineAvailability,
                  )
                }
                value={deadlineAvailability}
              >
                {DEADLINE_AVAILABILITY.map((option) => (
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
                onChange={(event) => updateSortFilter(event.target.value as SortFilter)}
                value={sortFilter}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span className="form-field__label">Minimum amount</span>
              <input
                className="text-input"
                inputMode="numeric"
                onChange={(event) => updateMinAmount(event.target.value)}
                placeholder="10000"
                value={minAmount}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Maximum amount</span>
              <input
                className="text-input"
                inputMode="numeric"
                onChange={(event) => updateMaxAmount(event.target.value)}
                placeholder="30000"
                value={maxAmount}
              />
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
                onClick={() => updateCountryFilter(filter.value)}
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
                data-testid={
                  filter.value === "artificial intelligence" ? "field-filter-ai" : undefined
                }
                key={filter.value}
                onClick={() => updateFieldFilter(filter.value)}
                type="button"
              >
                {filter.label}
              </button>
            ))}
          </div>

          <div className="dashboard-actions">
            <button className="auth-link auth-link--secondary" onClick={clearAllFilters} type="button">
              Clear filters
            </button>
            <p className="field-note">
              {state.items.length > 0
                ? `${(state.page - 1) * state.pageSize + 1}-${(state.page - 1) * state.pageSize + state.items.length} of ${state.total}`
                : `0 of ${state.total}`} visible
            </p>
          </div>
        </article>

        <div className="collection-grid">
          <section className="surface-card">
            <PageHeader
              eyebrow="Trust boundary"
              title="Published records only"
              description="This catalog is intentionally narrower than a generic scholarship directory so the facts stay dependable."
            />
            <div className="split-panel">
              <article className="data-callout">
                <p className="list-label">Validated record facts</p>
                <p className="body-copy">
                  Title, provider, country, deadline, and structured filters come from
                  published scholarship records.
                </p>
              </article>
              <article className="guidance-callout">
                <p className="list-label">What this page does not do</p>
                <p className="body-copy">
                  It does not guess fit on your behalf. That happens later in the
                  recommendation workspace once a profile is saved.
                </p>
              </article>
            </div>
          </section>

          {state.error ? (
            <section className="surface-card" data-testid="scholarship-browse-error">
              <PageHeader
                eyebrow="Catalog status"
                title="The scholarship catalog could not load."
                description={state.error}
              />
            </section>
          ) : null}

          {appliedFilterPills.length > 0 ? (
            <section className="surface-card">
              <PageHeader
                eyebrow="Current filters"
                title="The active search state is visible at a glance"
                description="ScholarAI shows why the current result set is narrow instead of hiding those constraints."
                compact
              />
              <div className="meta-row">
                {appliedFilterPills.map((pill) => (
                  <StatusBadge key={pill} label={pill} variant="generated" />
                ))}
              </div>
            </section>
          ) : null}

          <section className="surface-card">
            <PageHeader
              eyebrow="Published results"
              title="Review each opportunity before you save it"
              description="Every result keeps the factual essentials close and the next action obvious."
            />
            {state.isLoading ? (
              <p className="body-copy">Loading published scholarships.</p>
            ) : state.items.length > 0 ? (
              <>
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
                            Open the full record to inspect requirements, funding shape,
                            validation timing, and the published source before you save it.
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
                <div className="dashboard-actions scholarship-pagination">
                  <button
                    className="auth-link auth-link--secondary"
                    disabled={state.page <= 1 || state.isLoading}
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    type="button"
                  >
                    Previous page
                  </button>
                  <StatusBadge label={`Page ${state.page}`} variant="neutral" />
                  <button
                    className="auth-link auth-link--secondary"
                    disabled={!state.hasMore || state.isLoading}
                    onClick={() => setPage((current) => current + 1)}
                    type="button"
                  >
                    Next page
                  </button>
                </div>
              </>
            ) : (
              <div className="empty-panel">
                <p className="body-copy">
                  No published scholarships match the current filters. Try widening the
                  deadline window, clearing the provider search, or switching to all fields.
                </p>
              </div>
            )}
          </section>
        </div>
      </section>
    </AppShell>
  );
}
