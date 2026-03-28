"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/feedback-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard } from "@/components/ui/skeleton";
import { ScholarshipCompareTable } from "@/components/scholarships/scholarship-compare-table";
import { apiRequest } from "@/lib/api";
import type { ApiError, ScholarshipDetail } from "@/lib/types";

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

type CompareState = {
  isLoading: boolean;
  error: string | null;
  items: ScholarshipDetail[];
};

export function ScholarshipCompareShell() {
  const searchParams = useSearchParams();
  const compareIds = useMemo(
    () => parseCompareIds(searchParams.get("ids")).slice(0, MAX_COMPARE_ITEMS),
    [searchParams],
  );
  const [state, setState] = useState<CompareState>({
    isLoading: false,
    error: null,
    items: [],
  });

  useEffect(() => {
    let isActive = true;

    if (compareIds.length === 0) {
      return;
    }

    const loadCompare = async () => {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const details = await Promise.all(
          compareIds.map((id) => apiRequest<ScholarshipDetail>(`/scholarships/${id}`)),
        );
        if (!isActive) return;
        setState({
          isLoading: false,
          error: null,
          items: details,
        });
      } catch (caught) {
        if (!isActive) return;
        const error = caught as ApiError;
        setState({
          isLoading: false,
          error: error.message,
          items: [],
        });
      }
    };

    void loadCompare();

    return () => {
      isActive = false;
    };
  }, [compareIds]);

  return (
    <AppShell
      eyebrow="Scholarship compare"
      title="Compare scholarships side by side."
      description="Use this table to evaluate fit, funding, deadlines, and requirements from published records."
    >
      <section className="surface-card" data-testid="scholarship-compare-shell">
        <PageHeader
          eyebrow="Selection"
          title="Compare selection"
          description={`Comparing ${compareIds.length} scholarship${compareIds.length === 1 ? "" : "s"}.`}
        />
        <div className="dashboard-actions">
          <Link className="nav-link" href="/scholarships">
            Back to browse
          </Link>
        </div>
      </section>

      {compareIds.length > 0 && state.error ? (
        <ErrorState
          testId="scholarship-compare-error"
          title="Could not load scholarship comparison."
          description={state.error}
          action={
            <Link className="nav-link" href="/scholarships">
              Return to scholarships
            </Link>
          }
        />
      ) : null}

      {compareIds.length > 0 && state.isLoading ? (
        <section className="surface-card">
          <div className="recommendation-list">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </section>
      ) : null}

      {!state.isLoading && !state.error && compareIds.length === 0 ? (
        <section className="surface-card">
          <EmptyState
            title="Nothing to compare yet"
            description="Select scholarships from browse cards or detail pages, then open compare."
            action={
              <Link className="auth-link auth-link--primary" href="/scholarships">
                Browse scholarships
              </Link>
            }
          />
        </section>
      ) : null}

      {!state.isLoading && !state.error && compareIds.length > 0 && state.items.length > 0 ? (
        <section className="surface-card">
          <ScholarshipCompareTable items={state.items} />
        </section>
      ) : null}
    </AppShell>
  );
}
