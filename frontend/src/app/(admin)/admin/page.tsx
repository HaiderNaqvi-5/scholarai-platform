"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, FileText, GraduationCap, Library, MessageSquare, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/section-header";
import { endpoints } from "@/lib/api";

export default function AdminOverviewPage() {
  const platformQ = useQuery({
    queryKey: ["analytics", "platform"],
    queryFn: endpoints.analytics.platform,
  });
  const healthQ = useQuery({
    queryKey: ["analytics", "health"],
    queryFn: endpoints.analytics.health,
    refetchInterval: 60_000,
  });

  return (
    <div data-testid="admin-overview" className="mx-auto max-w-6xl space-y-5">
      <PageHeader
        title="Admin overview"
        description="Platform health, KPI alerts, and roll-up counts."
      />

      {healthQ.data && healthQ.data.kpi_alerts.length > 0 ? (
        <Card className="caution-stripe">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-caution" strokeWidth={2} />
              <CardTitle>{healthQ.data.kpi_alerts.length} active KPI alert(s)</CardTitle>
            </div>
          </CardHeader>
          <CardBody>
            <ul className="space-y-2">
              {healthQ.data.kpi_alerts.map((a, i) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  <Badge
                    tone={
                      a.severity === "critical"
                        ? "danger"
                        : a.severity === "warn"
                          ? "caution"
                          : "neutral"
                    }
                  >
                    {a.severity}
                  </Badge>
                  <span className="font-mono text-xs text-ink-subtle">{a.domain}</span>
                  <span className="text-ink">{a.message}</span>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      ) : null}

      {platformQ.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : platformQ.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              icon={<Users className="size-4" strokeWidth={2} />}
              label="Total users"
              value={platformQ.data.total_users}
            />
            <Stat
              icon={<GraduationCap className="size-4" strokeWidth={2} />}
              label="Students"
              value={platformQ.data.student_count}
            />
            <Stat
              icon={<Library className="size-4" strokeWidth={2} />}
              label="Scholarships"
              value={platformQ.data.total_scholarships}
            />
            <Stat
              icon={<Activity className="size-4" strokeWidth={2} />}
              label="Mentors"
              value={platformQ.data.mentor_count}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Stat
              icon={<FileText className="size-4" strokeWidth={2} />}
              label="Documents"
              value={platformQ.data.documents_count}
            />
            <Stat
              icon={<MessageSquare className="size-4" strokeWidth={2} />}
              label="Interview sessions"
              value={platformQ.data.interview_sessions_count}
            />
            <Stat
              icon={<Activity className="size-4" strokeWidth={2} />}
              label="Applications"
              value={platformQ.data.applications_count}
            />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Recent ingestion runs</CardTitle>
            </CardHeader>
            <CardBody>
              <ul className="space-y-1 text-sm">
                {platformQ.data.ingestion_runs_recent.map((r, i) => (
                  <li key={i} className="flex items-center justify-between">
                    <span className="text-ink">{r.status}</span>
                    <span className="font-mono text-ink">{r.count}</span>
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <Card>
      <CardBody>
        <div className="flex items-center gap-2 text-ink-subtle">
          {icon}
          <span className="font-mono text-[11px] uppercase tracking-[0.06em]">{label}</span>
        </div>
        <p className="mt-2 font-mono text-[28px] font-semibold tabular-nums text-ink-deep">
          {value.toLocaleString()}
        </p>
      </CardBody>
    </Card>
  );
}
