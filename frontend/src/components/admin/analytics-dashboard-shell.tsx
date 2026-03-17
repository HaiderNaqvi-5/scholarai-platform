"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonLine } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { getAdminAnalytics } from "@/lib/api";
import type { PlatformAnalyticsResponse } from "@/lib/types";

export function AnalyticsDashboardShell() {
  const { accessToken } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<PlatformAnalyticsResponse | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    const loadData = async () => {
      try {
        setIsLoading(true);
        const data = await getAdminAnalytics(accessToken);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message || "Failed to load platform analytics.");
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();
  }, [accessToken]);

  return (
    <AppShell
      eyebrow="Admin Dashboard"
      title="Platform Health & Metrics"
      description="Monitor user activity, scholarship ingestion, and processing health."
    >
      {isLoading ? (
        <section className="metrics-grid">
          {[1, 2, 3, 4].map((i) => (
            <article key={i} className="data-point">
              <SkeletonLine count={2} />
            </article>
          ))}
        </section>
      ) : analytics ? (
        <>
          <section className="metrics-grid mb-8">
            <article className="data-point">
              <p className="data-point__label">Users</p>
              <strong>{analytics.total_users}</strong>
              <div className="flex gap-2 text-xs opacity-75 mt-2">
                <span>{analytics.student_count} Students</span>
                <span>{analytics.mentor_count} Mentors</span>
              </div>
            </article>
            <article className="data-point">
              <p className="data-point__label">Scholarships</p>
              <strong>{analytics.total_scholarships}</strong>
              <p className="body-copy">Total catalog size</p>
            </article>
            <article className="data-point">
              <p className="data-point__label">Applications</p>
              <strong>{analytics.submitted_applications}</strong>
              <p className="body-copy">
                Out of {analytics.total_applications} started
              </p>
            </article>
            <article className="data-point">
              <p className="data-point__label">AI Usage</p>
              <strong>
                {analytics.total_documents + analytics.total_interview_sessions}
              </strong>
              <div className="flex gap-2 text-xs opacity-75 mt-2">
                <span>{analytics.total_documents} Docs</span>
                <span>{analytics.total_interview_sessions} Interviews</span>
              </div>
            </article>
          </section>

          <div className="dashboard-grid">
            <article className="surface-card">
              <PageHeader
                eyebrow="Data Supply"
                title="Ingestion Health"
                description="Status of automated scholarship discovery and import tasks."
              />
              <div className="surface-list">
                <div className="list-item-btn no-hover">
                  <p className="list-heading">Total Discovery Runs</p>
                  <strong>{analytics.ingestion_runs_total}</strong>
                </div>
                <div className="list-item-btn no-hover">
                  <p className="list-heading">Failed Runs</p>
                  <strong
                    className={
                      analytics.ingestion_runs_failed > 0 ? "text-red-600" : ""
                    }
                  >
                    {analytics.ingestion_runs_failed}
                  </strong>
                </div>
              </div>
            </article>

            <article className="surface-card">
              <PageHeader
                eyebrow="System"
                title="Resources & Logs"
                description="Quick links to monitoring and infrastructure logs."
              />
              <div className="grid grid-cols-1 gap-4 mt-6">
                <button type="button" className="nav-link text-left">
                  Open Celery Dashboard (Flower)
                </button>
                <button type="button" className="nav-link text-left">
                  View Sentry Errors
                </button>
                <button type="button" className="nav-link text-left">
                  Database Performance logs
                </button>
              </div>
            </article>
          </div>
        </>
      ) : (
        <EmptyState
          title="No data"
          description="Could not calculate analytics at this time."
        />
      )}

      {error && (
        <section className="surface-card mt-6 border-red-200 bg-red-50">
          <p className="text-red-700 font-medium">{error}</p>
        </section>
      )}
    </AppShell>
  );
}
