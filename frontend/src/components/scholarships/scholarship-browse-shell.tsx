"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
import { DiscoveryFilterBar } from "@/components/scholarships/discovery-filter-bar";
import { motion, AnimatePresence } from "framer-motion";
import { Calendar, Building2, ExternalLink } from "lucide-react";

// Filter types removed for brevity as they are now handled by discovery-filter-bar

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
  const [countryFilter, setCountryFilter] = useState<string>("all");
  const [fieldFilter, setFieldFilter] = useState<string>("all");
  const [providerFilter, setProviderFilter] = useState("");
  const [fundingFilter, setFundingFilter] = useState<string>("all");
  const [deadlineWindow, setDeadlineWindow] = useState<string>("all");
  const [deadlineAvailability, setDeadlineAvailability] =
    useState<string>("all");
  const [sortFilter, setSortFilter] = useState<string>("deadline");
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

  const handleSaveToggle = async (scholarshipId: string, isSaved: boolean) => {
    if (!accessToken) return;

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

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const item = {
    hidden: { opacity: 0, scale: 0.98, y: 10 },
    show: { opacity: 1, scale: 1, y: 0 }
  };

  return (
    <AppShell
      title="Discovery Hub"
      description="Global Scholarship Repository"
      hideHeader
    >
      <header className="mb-12">
        <motion.div 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3 mb-4"
        >
          <Building2 size={16} className="text-cobalt-600" />
          <span className="text-xs font-bold uppercase tracking-widest text-neutral-400">
            Global Knowledge Base
          </span>
        </motion.div>
        <h1 className="text-5xl font-semibold tracking-tight text-neutral-900">
          Search Scholarships.
        </h1>
      </header>

      <DiscoveryFilterBar 
        searchQuery={searchQuery}
        onSearchChange={(v) => updateAndReset(setSearchQuery)(v)}
        filters={{
          country: countryFilter,
          field: fieldFilter,
          funding: fundingFilter,
          sort: sortFilter
        }}
        onFilterChange={(key, val) => {
          if (key === "country") updateAndReset(setCountryFilter)(val);
          if (key === "field") updateAndReset(setFieldFilter)(val);
          if (key === "funding") updateAndReset(setFundingFilter)(val);
        }}
        onClear={clearAllFilters}
        resultsCount={state.total}
      />

      {state.error && (
        <motion.section 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="glass-surface p-6 mb-8 border-coral-600/20 bg-coral-600/5"
        >
          <PageHeader eyebrow="Repo Error" title="Connection Interrupted" description={state.error} />
        </motion.section>
      )}

      <div className="collection-workspace">
        <AnimatePresence mode="wait">
          {state.isLoading ? (
            <motion.div 
               key="loading"
               initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
               className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            >
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </motion.div>
          ) : (
            <motion.div
              key="results"
              variants={container}
              initial="hidden"
              animate="show"
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            >
              {state.items.length > 0 ? (
                state.items.map((itemData) => {
                  const isSaved = state.savedIds.has(itemData.scholarship_id);
                  return (
                    <motion.article 
                      variants={item}
                      key={itemData.scholarship_id}
                      className="glass-surface flex flex-col h-full rounded-2xl group overflow-hidden hover:border-cobalt-600/30 transition-all"
                    >
                      <div className="flex-1 p-8">
                        <div className="flex justify-between items-start mb-6">
                           <div className="px-3 py-1 bg-neutral-900 text-white text-[10px] font-bold rounded-md uppercase tracking-widest">
                             {itemData.country_code}
                           </div>
                           {itemData.deadline_at && (
                             <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500">
                               <Calendar size={14} />
                               {new Date(itemData.deadline_at).toLocaleDateString()}
                             </div>
                           )}
                        </div>

                        <h3 className="text-xl font-semibold text-neutral-900 line-clamp-2 leading-snug mb-4 group-hover:text-cobalt-600 transition-colors">
                          {itemData.title}
                        </h3>
                        
                        <div className="flex items-center gap-3 text-sm text-neutral-500 mb-8">
                          <Building2 size={16} className="text-neutral-300" />
                          <span className="truncate">{itemData.provider_name || 'Global Provider'}</span>
                        </div>

                        <div className="flex flex-wrap gap-2">
                           <StatusBadge label="Verified Data" variant="validated" />
                           <StatusBadge label="Academic Grant" variant="neutral" />
                        </div>
                      </div>

                      <div className="p-4 bg-neutral-50 border-t border-white/5 flex gap-3">
                        <Link 
                          href={`/scholarships/${itemData.scholarship_id}`}
                          className="flex-1 flex items-center justify-center gap-2 text-sm font-bold text-neutral-700 bg-white border border-neutral-200 py-3 rounded-xl hover:bg-neutral-50 transition-all"
                        >
                          Details
                          <ExternalLink size={14} />
                        </Link>
                        {isAuthenticated && (
                          <button
                            disabled={state.isSaving === itemData.scholarship_id}
                            onClick={() => void handleSaveToggle(itemData.scholarship_id, isSaved)}
                            className={`flex-1 text-sm font-bold py-3 rounded-xl transition-all ${isSaved ? 'bg-neutral-200 text-neutral-500' : 'bg-neutral-900 text-white hover:bg-black shadow-lg shadow-neutral-900/10'}`}
                          >
                            {state.isSaving === itemData.scholarship_id ? 'Syncing...' : isSaved ? 'Saved' : 'Save'}
                          </button>
                        )}
                      </div>
                    </motion.article>
                  );
                })
              ) : (
                <div className="col-span-full py-24 text-center">
                  <EmptyState title="Repository Clear" description="No scholarships match the current knowledge filters." />
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {state.total > state.pageSize && (
          <footer className="mt-16 flex items-center justify-center gap-4">
             <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={state.page === 1}
                className="px-6 py-3 rounded-xl border border-neutral-200 font-bold text-sm text-neutral-600 hover:bg-neutral-50 disabled:opacity-50 transition-all"
             >
               Prev
             </button>
             <span className="px-4 py-2 bg-neutral-100 rounded-lg text-xs font-bold text-neutral-500">
               Batch {state.page}
             </span>
             <button 
                onClick={() => setPage(p => p + 1)}
                disabled={!state.hasMore}
                className="px-6 py-3 rounded-xl border border-neutral-200 font-bold text-sm text-neutral-600 hover:bg-neutral-50 disabled:opacity-50 transition-all"
             >
               Next
             </button>
          </footer>
        )}
      </div>
    </AppShell>
  );
}
