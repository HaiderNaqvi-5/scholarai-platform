"use client";

/**
 * /tracker — Pakistan-pivot application Kanban (PRD §6).
 *
 * 6 columns matching the backend TrackerStage enum, native HTML5 drag-and-drop
 * (cloned pattern from /saved), 14-key per-card document checklist with
 * hec_attestation surfaced as Pakistan-specific. Free tier capped at 3 items —
 * the create form catches the 402 and renders <UpgradeWall />.
 */

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  GripVertical,
  Plus,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints, isPlanRequiredError } from "@/lib/api";
import type {
  PlanRequiredDetail,
  TrackerItem,
  TrackerItemCreateRequest,
  TrackerListResponse,
} from "@/lib/api";
import {
  CHECKLIST_KEYS,
  CHECKLIST_LABELS,
  checklistProgress,
  type TrackerChecklist,
} from "@/lib/tracker/checklist";
import {
  STAGE_META,
  TRACKER_STAGES,
  type TrackerStage,
} from "@/lib/tracker/stages";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { KanbanColumn } from "@/components/kanban/KanbanColumn";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { UpgradeWall } from "@/components/UpgradeWall";
import { cn } from "@/lib/utils";


export default function TrackerPage() {
  const qc = useQueryClient();
  const trackerQ = useQuery({
    queryKey: ["tracker"],
    queryFn: endpoints.tracker.list,
  });

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [overCol, setOverCol] = useState<TrackerStage | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [createWall, setCreateWall] = useState<PlanRequiredDetail | null>(null);

  const setStage = useMutation({
    mutationFn: async ({ id, stage }: { id: string; stage: TrackerStage }) =>
      endpoints.tracker.setStage(id, stage),
    onMutate: async ({ id, stage }) => {
      await qc.cancelQueries({ queryKey: ["tracker"] });
      const prev = qc.getQueryData<TrackerListResponse>(["tracker"]);
      qc.setQueryData<TrackerListResponse | undefined>(["tracker"], (old) =>
        old
          ? { ...old, items: old.items.map((i) => (i.id === id ? { ...i, stage } : i)) }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["tracker"], ctx?.prev);
      toast.error("Couldn't move card. Reverted.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["tracker"] }),
  });

  const setChecklist = useMutation({
    mutationFn: async ({
      id,
      checklist,
    }: {
      id: string;
      checklist: TrackerChecklist;
    }) => endpoints.tracker.setChecklist(id, checklist),
    onMutate: async ({ id, checklist }) => {
      await qc.cancelQueries({ queryKey: ["tracker"] });
      const prev = qc.getQueryData<TrackerListResponse>(["tracker"]);
      qc.setQueryData<TrackerListResponse | undefined>(["tracker"], (old) =>
        old
          ? {
              ...old,
              items: old.items.map((i) =>
                i.id === id ? { ...i, document_checklist: checklist } : i,
              ),
            }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["tracker"], ctx?.prev);
      toast.error("Couldn't save checklist. Reverted.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["tracker"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => endpoints.tracker.remove(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["tracker"] });
      const prev = qc.getQueryData<TrackerListResponse>(["tracker"]);
      qc.setQueryData<TrackerListResponse | undefined>(["tracker"], (old) =>
        old
          ? { ...old, items: old.items.filter((i) => i.id !== id), total: old.total - 1 }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["tracker"], ctx?.prev);
      toast.error("Couldn't remove.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["tracker"] }),
  });

  const create = useMutation({
    mutationFn: (body: TrackerItemCreateRequest) => endpoints.tracker.create(body),
    onSuccess: (item) => {
      setCreateWall(null);
      setShowForm(false);
      qc.setQueryData<TrackerListResponse | undefined>(["tracker"], (old) =>
        old
          ? { ...old, items: [...old.items, item], total: old.total + 1 }
          : old,
      );
      toast.success("Added to your tracker.");
    },
    onError: (err) => {
      if (isPlanRequiredError(err)) {
        setCreateWall(err.detail);
        return;
      }
      const msg = err instanceof ApiError ? err.message : "Couldn't add item.";
      toast.error(msg);
    },
  });

  function onDrop(stage: TrackerStage) {
    if (!draggingId) return;
    const item = trackerQ.data?.items.find((i) => i.id === draggingId);
    if (item && item.stage !== stage) {
      setStage.mutate({ id: draggingId, stage });
    }
    setDraggingId(null);
    setOverCol(null);
  }

  // Stabilise the items reference so the two downstream useMemos don't see
  // a fresh `[]` literal on every render when the query hasn't resolved.
  const items = useMemo(
    () => trackerQ.data?.items ?? [],
    [trackerQ.data?.items],
  );
  const planLimit = trackerQ.data?.plan_limit ?? null;
  const isFree = trackerQ.data?.plan === "free";

  // Group items into Kanban columns once per items reference rather than
  // filtering 6× per render across all items.
  const itemsByStage = useMemo(() => {
    const map = new Map<TrackerStage, TrackerItem[]>(
      TRACKER_STAGES.map((s) => [s, []]),
    );
    for (const item of items) {
      map.get(item.stage)?.push(item);
    }
    return map;
  }, [items]);

  const urgentBanner = useMemo(() => buildUrgentBanner(items), [items]);

  if (trackerQ.isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">
        {STAGE_META.map((c) => (
          <Skeleton key={c.stage} className="h-96 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px]" data-testid="tracker-board">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl text-ink">Application tracker</h1>
          <p className="mt-1 text-ink-muted">
            {items.length} {items.length === 1 ? "application" : "applications"}
            {planLimit != null ? ` · free cap ${planLimit}` : ""} · drag cards
            between columns to update stage.
          </p>
        </div>
        <Button
          onClick={() => {
            setShowForm((s) => !s);
            setCreateWall(null);
          }}
        >
          <Plus className="size-4" aria-hidden /> Add application
        </Button>
      </header>

      {urgentBanner && (
        <div
          role="status"
          className="mb-4 flex items-start gap-2 rounded-[16px] border border-caution/30 bg-caution-soft/60 p-4"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-caution" aria-hidden />
          <p className="text-sm text-ink">{urgentBanner}</p>
        </div>
      )}

      {showForm && !createWall && (
        <CreateForm
          submitting={create.isPending}
          onCancel={() => setShowForm(false)}
          onSubmit={(body) => create.mutate(body)}
        />
      )}

      {createWall && (
        <UpgradeWall
          detail={createWall}
          featureName="Application tracker"
          showElite={false}
          className="mb-6"
        />
      )}

      {items.length === 0 ? (
        <EmptyState onAdd={() => setShowForm(true)} />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">
          {STAGE_META.map((col) => {
            const colItems = itemsByStage.get(col.stage) ?? [];
            return (
              <KanbanColumn
                key={col.stage}
                label={col.label}
                count={colItems.length}
                tone={col.tone}
                isOver={overCol === col.stage}
                onDragOver={(e) => {
                  e.preventDefault();
                  // Avoid a setState burst on every mousemove during drag.
                  if (overCol !== col.stage) setOverCol(col.stage);
                }}
                onDragLeave={() =>
                  setOverCol((c) => (c === col.stage ? null : c))
                }
                onDrop={() => onDrop(col.stage)}
              >
                {colItems.map((item) => (
                  <TrackerCard
                    key={item.id}
                    item={item}
                    dragging={draggingId === item.id}
                    expanded={expandedId === item.id}
                    onDragStart={() => setDraggingId(item.id)}
                    onDragEnd={() => {
                      setDraggingId(null);
                      setOverCol(null);
                    }}
                    onToggleExpand={() =>
                      setExpandedId((id) => (id === item.id ? null : item.id))
                    }
                    onChecklistChange={(checklist) =>
                      setChecklist.mutate({ id: item.id, checklist })
                    }
                    onRemove={() => remove.mutate(item.id)}
                  />
                ))}
              </KanbanColumn>
            );
          })}
        </div>
      )}

      {isFree && (
        <p className="mt-6 text-center text-xs text-ink-muted">
          Free accounts can track up to {planLimit ?? 3} applications.
          Need more?{" "}
          <a href="/upgrade?plan=pro" className="underline">
            Upgrade to Pro
          </a>
          .
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

function TrackerCard({
  item,
  dragging,
  expanded,
  onDragStart,
  onDragEnd,
  onToggleExpand,
  onChecklistChange,
  onRemove,
}: {
  item: TrackerItem;
  dragging: boolean;
  expanded: boolean;
  onDragStart: () => void;
  onDragEnd: () => void;
  onToggleExpand: () => void;
  onChecklistChange: (c: TrackerChecklist) => void;
  onRemove: () => void;
}) {
  const dl = deadlineLabel(item.deadline);
  const progress = checklistProgress(item.document_checklist);
  const title =
    item.program_name || item.university_name || "Untitled application";
  const subtitle = item.program_name ? item.university_name : null;

  return (
    <Card
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={cn(
        "cursor-grab active:cursor-grabbing",
        dragging && "opacity-50 ring-2 ring-[var(--color-ring)]",
      )}
    >
      <CardBody className="p-3">
        <div className="flex items-start gap-2">
          <GripVertical
            className="mt-1 size-4 shrink-0 text-ink-subtle"
            strokeWidth={2}
            aria-hidden
          />
          <div className="min-w-0 flex-1 space-y-2">
            <p className="line-clamp-2 font-display text-sm text-ink">{title}</p>
            {subtitle && (
              <p className="truncate text-xs text-ink-muted">{subtitle}</p>
            )}
            <div className="flex flex-wrap gap-1.5">
              {item.country && (
                <Badge tone="neutral">{item.country}</Badge>
              )}
              {dl && (
                <Badge
                  tone={
                    dl.tone === "urgent"
                      ? "danger"
                      : dl.tone === "soon"
                        ? "caution"
                        : "neutral"
                  }
                >
                  {dl.label}
                </Badge>
              )}
              <Badge tone="neutral">
                {progress.done}/{progress.total} docs
              </Badge>
            </div>
          </div>
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove application"
            className="rounded p-1 text-ink-subtle hover:bg-paper-warm hover:text-danger"
          >
            <Trash2 className="size-3.5" strokeWidth={2} />
          </button>
        </div>

        <button
          type="button"
          onClick={onToggleExpand}
          aria-expanded={expanded}
          className="mt-2 inline-flex items-center gap-1 text-xs text-ink-muted hover:text-ink"
        >
          {expanded ? (
            <ChevronUp className="size-3.5" />
          ) : (
            <ChevronDown className="size-3.5" />
          )}
          {expanded ? "Hide checklist" : "Document checklist"}
        </button>

        {expanded && (
          <ChecklistEditor
            checklist={item.document_checklist}
            onChange={onChecklistChange}
          />
        )}
      </CardBody>
    </Card>
  );
}

function ChecklistEditor({
  checklist,
  onChange,
}: {
  checklist: TrackerChecklist;
  onChange: (c: TrackerChecklist) => void;
}) {
  return (
    <ul className="mt-2 space-y-1.5 border-t border-[var(--color-border)] pt-2">
      {CHECKLIST_KEYS.map((key) => (
        <li key={key} className="flex items-start gap-2">
          <input
            id={`chk-${key}`}
            type="checkbox"
            checked={Boolean(checklist?.[key])}
            onChange={(e) =>
              onChange({ ...checklist, [key]: e.target.checked } as TrackerChecklist)
            }
            className="mt-0.5 size-4 shrink-0 cursor-pointer accent-[var(--color-validated)]"
          />
          <label
            htmlFor={`chk-${key}`}
            className={cn(
              "cursor-pointer text-xs leading-snug",
              checklist?.[key] ? "text-ink-subtle line-through" : "text-ink",
            )}
          >
            {CHECKLIST_LABELS[key]}
          </label>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Create form
// ---------------------------------------------------------------------------

function CreateForm({
  submitting,
  onCancel,
  onSubmit,
}: {
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (body: TrackerItemCreateRequest) => void;
}) {
  const [programName, setProgramName] = useState("");
  const [universityName, setUniversityName] = useState("");
  const [country, setCountry] = useState("");
  const [deadline, setDeadline] = useState("");
  const [stage, setStage] = useState<TrackerStage>("researching");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!programName && !universityName) {
      toast.error("Add a program or university name.");
      return;
    }
    onSubmit({
      program_name: programName || null,
      university_name: universityName || null,
      country: country ? country.toUpperCase().slice(0, 2) : null,
      stage,
      deadline: deadline || null,
    });
  }

  return (
    <Card className="mb-6 bg-paper-white">
      <CardBody>
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="t-program">Program name</Label>
            <Input
              id="t-program"
              placeholder="MS Computer Science"
              value={programName}
              onChange={(e) => setProgramName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="t-uni">University</Label>
            <Input
              id="t-uni"
              placeholder="University of Manchester"
              value={universityName}
              onChange={(e) => setUniversityName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="t-country">Country (2-letter)</Label>
            <Input
              id="t-country"
              maxLength={2}
              placeholder="GB"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="t-deadline">Deadline</Label>
            <Input
              id="t-deadline"
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="t-stage">Stage</Label>
            <select
              id="t-stage"
              value={stage}
              onChange={(e) => setStage(e.target.value as TrackerStage)}
              className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px] text-ink"
            >
              {TRACKER_STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <Button type="submit" loading={submitting}>
              Save
            </Button>
            <Button type="button" variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
      <h2 className="font-display text-xl text-ink">Nothing tracked yet</h2>
      <p className="mt-2 text-ink-muted">
        Add an application or scholarship from your{" "}
        <a href="/feed" className="underline">
          matches
        </a>{" "}
        to keep its deadline and document checklist in one place.
      </p>
      <div className="mt-5">
        <Button onClick={onAdd}>
          <Plus className="size-4" aria-hidden /> Add application
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers (deadline / urgent banner — checklistProgress lives in lib/tracker)
// ---------------------------------------------------------------------------

function deadlineLabel(deadline: string | null | undefined) {
  if (!deadline) return null;
  const target = new Date(deadline + "T00:00:00").getTime();
  if (Number.isNaN(target)) return null;
  const days = Math.ceil((target - Date.now()) / 86_400_000);
  if (days < 0) return { label: "Closed", days, tone: "passed" as const };
  if (days === 0) return { label: "Today", days, tone: "urgent" as const };
  if (days <= 30) return { label: `${days}d`, days, tone: "urgent" as const };
  if (days <= 60) return { label: `${days}d`, days, tone: "soon" as const };
  return { label: `${days}d`, days, tone: "ok" as const };
}

function buildUrgentBanner(items: TrackerItem[]): string | null {
  const urgent = items
    .map((i) => ({ i, dl: deadlineLabel(i.deadline) }))
    .filter((row) => row.dl && row.dl.days >= 0 && row.dl.days <= 30);
  if (urgent.length === 0) return null;
  const next = urgent.sort((a, b) => (a.dl!.days - b.dl!.days))[0];
  const title = next.i.program_name || next.i.university_name || "Application";
  const missing = checklistProgress(next.i.document_checklist);
  const stillMissing = missing.total - missing.done;
  return `${title} closes in ${next.dl!.days} day${next.dl!.days === 1 ? "" : "s"} — ${stillMissing} document${stillMissing === 1 ? "" : "s"} still missing.`;
}
