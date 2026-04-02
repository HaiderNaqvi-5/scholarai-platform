"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonCard } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
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
  { label: "All", value: "all" },
  { label: "Canada", value: "CA" },
  { label: "Fulbright", value: "US" },
] as const;

const FIELD_FILTERS = [
  { label: "All fields", value: "all" },
  { label: "Data Science", value: "data science" },
  { label: "AI", value: "artificial intelligence" },
  { label: "Analytics", value: "analytics" },
] as const;

const DEADLINE_WINDOWS = [
  { label: "Any", value: "all" },
  { label: "30 days", value: "30" },
  { label: "60 days", value: "60" },
  { label: "90 days", value: "90" },
] as const;

const DEADLINE_AVAILABILITY = [
  { label: "Any", value: "all" },
  { label: "Has deadline", value: "true" },
  { label: "No deadline", value: "false" },
] as const;

const FUNDING_TYPES = [
  { label: "Any type", value: "all" },
  { label: "Tuition award", value: "tuition_award" },
  { label: "Stipend", value: "stipend" },
  { label: "Fellowship", value: "fellowship" },
  { label: "Comprehensive", value: "comprehensive_award" },
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
const MAX_COMPARE_ITEMS = 4;

function parseCompareIds(raw: string | null): string[] {
  if (!raw) return [];
  return Array.from(
    new Set(
      raw
        .split(",")
        .map((value) => value.trim())
        .filter((value) => value.length > 0),
    ),
  );
}

export function ScholarshipBrowseShell() {
  const { accessToken, isAuthenticated, currentUser } = useAuth();
  const isTestUser = currentUser?.role?.toLowerCase() === "enduser_student";
  const router = useRouter();
  const searchParams = useSearchParams();
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

  const updateAndReset = <T,>(setter: (v: T) => void) => (value: T) => {
    setter(value);
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

        if (countryFilter !== "all") query.set("country_code", countryFilter);
        if (fieldFilter !== "all") query.set("field_tag", fieldFilter);
        if (providerFilter.trim()) query.set("provider", providerFilter.trim());
        if (fundingFilter !== "all") query.set("funding_type", fundingFilter);
        if (deadlineWindow !== "all") query.set("deadline_within_days", deadlineWindow);
        if (deadlineAvailability !== "all") query.set("has_deadline", deadlineAvailability);
        if (searchQuery.trim()) query.set("query", searchQuery.trim());
        if (minAmount.trim()) query.set("min_amount", minAmount.trim());
        if (maxAmount.trim()) query.set("max_amount", maxAmount.trim());

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

        if (!isActive) return;

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
        if (!isActive) return;
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
      filters.country_code ? `Country: ${filters.country_code}` : null,
      filters.degree_level ? `Degree: ${filters.degree_level}` : null,
      filters.field_tag ? `Field: ${filters.field_tag}` : null,
      filters.provider ? `Provider: ${filters.provider}` : null,
      filters.funding_type ? `Funding: ${filters.funding_type.replaceAll("_", " ")}` : null,
      filters.min_amount !== null ? `Min $${filters.min_amount}` : null,
      filters.max_amount !== null ? `Max $${filters.max_amount}` : null,
      filters.has_deadline === true
        ? "Has deadline"
        : filters.has_deadline === false
          ? "No deadline"
          : null,
      filters.deadline_within_days
        ? `Within ${filters.deadline_within_days} days`
        : null,
    ].filter(Boolean) as string[];
  }, [state.appliedFilters]);

  const compareIds = useMemo(
    () => parseCompareIds(searchParams.get("ids")),
    [searchParams],
  );

  const compareHref = useMemo(() => {
    const ids = compareIds.join(",");
    return ids ? `/scholarships/compare?ids=${encodeURIComponent(ids)}` : "/scholarships/compare";
  }, [compareIds]);

  const updateCompareIds = (nextIds: string[]) => {
    const params = new URLSearchParams(searchParams.toString());
    if (nextIds.length > 0) {
      params.set("ids", nextIds.join(","));
    } else {
      params.delete("ids");
    }

    const query = params.toString();
    router.replace(query ? `/scholarships?${query}` : "/scholarships", { scroll: false });
  };

  const toggleCompare = (scholarshipId: string) => {
    if (compareIds.includes(scholarshipId)) {
      updateCompareIds(compareIds.filter((id) => id !== scholarshipId));
      return;
    }

    if (compareIds.length >= MAX_COMPARE_ITEMS) return;
    updateCompareIds([...compareIds, scholarshipId]);
  };

  const handleSaveToggle = async (scholarshipId: string, isSaved: boolean) => {
    if (!accessToken || isTestUser) return;

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
      eyebrow="Scholarships"
      title="Browse published scholarships."
      description="A curated catalog with structured filters, verified deadlines, and clear data provenance."
      intro={
        <div className="meta-row">
          <StatusBadge label="Published records" variant="validated" />
          <StatusBadge label={`${state.total} results`} variant="neutral" />
        </div>
      }
    >
      <section className="workspace-layout" data-testid="scholarship-browse-shell">
        <article className="surface-panel scholarship-filter-rail">
          <PageHeader
            eyebrow="Filters"
            title="Narrow your search"
            description="Adjust filters to find scholarships that match your criteria."
          />
          <div className="form-grid">
            <label className="form-field">
              <span className="form-field__label">Search</span>
              <input
                className="text-input"
                data-testid="scholarship-search-input"
                onChange={(event) => updateAndReset(setSearchQuery)(event.target.value)}
                placeholder="Title or provider"
                value={searchQuery}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Provider</span>
              <input
                className="text-input"
                data-testid="scholarship-provider-input"
                onChange={(event) => updateAndReset(setProviderFilter)(event.target.value)}
                placeholder="University name"
                value={providerFilter}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Funding type</span>
              <select
                className="text-input"
                data-testid="scholarship-funding-select"
                onChange={(event) =>
                  updateAndReset(setFundingFilter)(event.target.value as FundingTypeFilter)
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
                  updateAndReset(setDeadlineWindow)(event.target.value as DeadlineWindow)
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
              <span className="form-field__label">Deadline status</span>
              <select
                className="text-input"
                onChange={(event) =>
                  updateAndReset(setDeadlineAvailability)(
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
              <span className="form-field__label">Sort</span>
              <select
                className="text-input"
                onChange={(event) => updateAndReset(setSortFilter)(event.target.value as SortFilter)}
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
              <span className="form-field__label">Min amount</span>
              <input
                className="text-input"
                inputMode="numeric"
                onChange={(event) => updateAndReset(setMinAmount)(event.target.value)}
                placeholder="10000"
                value={minAmount}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Max amount</span>
              <input
                className="text-input"
                inputMode="numeric"
                onChange={(event) => updateAndReset(setMaxAmount)(event.target.value)}
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
                onClick={() => updateAndReset(setCountryFilter)(filter.value)}
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
                onClick={() => updateAndReset(setFieldFilter)(filter.value)}
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
                ? `${(state.page - 1) * state.pageSize + 1}–${(state.page - 1) * state.pageSize + state.items.length} of ${state.total}`
                : `0 of ${state.total}`}
            </p>
          </div>
        </article>

        <div className="collection-grid">
          {state.error ? (
            <section className="surface-card" data-testid="scholarship-browse-error">
              <PageHeader
                eyebrow="Error"
                title="Could not load scholarships."
                description={state.error}
              />
            </section>
          ) : null}

          {appliedFilterPills.length > 0 ? (
            <section className="meta-row">
              {appliedFilterPills.map((pill) => (
                <StatusBadge key={pill} label={pill} variant="generated" />
              ))}
            </section>
          ) : null}

          <section className="surface-card">
            <PageHeader
              eyebrow="Results"
              title="Published scholarships"
              description="Each record has been verified and published with source provenance."
            />
            <div className="dashboard-actions">
              <Link className="auth-link auth-link--secondary" href={compareHref}>
                Compare selected ({compareIds.length})
              </Link>
              {compareIds.length > 0 ? (
                <button
                  className="auth-link auth-link--secondary"
                  onClick={() => updateCompareIds([])}
                  type="button"
                >
                  Clear compare
                </button>
              ) : null}
              <p className="field-note">Select up to {MAX_COMPARE_ITEMS} scholarships.</p>
            </div>
            {state.isLoading ? (
              <div className="recommendation-list">
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
              </div>
            ) : state.items.length > 0 ? (
              <>
                <div className="recommendation-list">
                  {state.items.map((item) => {
                    const isSaved = state.savedIds.has(item.scholarship_id);
                    const isCompared = compareIds.includes(item.scholarship_id);
                    const canAddToCompare =
                      isCompared || compareIds.length < MAX_COMPARE_ITEMS;
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
                        </div>
                        <div className="dashboard-actions">
                          <Link className="nav-link" href={`/scholarships/${item.scholarship_id}`}>
                            View details
                          </Link>
                          <button
                            className={
                              isCompared
                                ? "auth-link auth-link--secondary"
                                : "auth-link auth-link--primary"
                            }
                            disabled={!canAddToCompare}
                            onClick={() => toggleCompare(item.scholarship_id)}
                            type="button"
                            aria-pressed={isCompared}
                          >
                            {isCompared ? "Added to compare" : "Add to compare"}
                          </button>
                          {isAuthenticated ? (
                            <button
                              className={
                                isSaved
                                  ? "auth-link auth-link--secondary"
                                  : "auth-link auth-link--primary"
                              }
                              disabled={state.isSaving === item.scholarship_id || isTestUser}
                              onClick={() =>
                                void handleSaveToggle(item.scholarship_id, isSaved)
                              }
                              type="button"
                            >
                              {state.isSaving === item.scholarship_id
                                ? "Updating…"
                                : isTestUser
                                  ? "Test-user locked"
                                : isSaved
                                  ? "Saved"
                                  : "Save"}
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
                    Previous
                  </button>
                  <StatusBadge label={`Page ${state.page}`} variant="neutral" />
                  <button
                    className="auth-link auth-link--secondary"
                    disabled={!state.hasMore || state.isLoading}
                    onClick={() => setPage((current) => current + 1)}
                    type="button"
                  >
                    Next
                  </button>
                </div>
              </>
            ) : (
              <EmptyState
                title="No scholarships found"
                description="No scholarships match the current filters. Try widening your search or clearing filters."
              />
            )}
          </section>
        </div>
      </section>
    </AppShell>
  );
}
