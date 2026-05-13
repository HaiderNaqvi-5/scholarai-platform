"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, GripVertical, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { endpoints } from "@/lib/api";
import type { SavedOpportunity, SavedStatus } from "@/lib/api";
import { formatDeadline } from "@/lib/utils";

const COLUMNS: { status: SavedStatus; label: string; tone: "neutral" | "validated" | "caution" | "danger" }[] = [
  { status: "saved", label: "Saved", tone: "neutral" },
  { status: "in_progress", label: "In progress", tone: "validated" },
  { status: "applied", label: "Applied", tone: "validated" },
  { status: "closed", label: "Closed", tone: "caution" },
];

export default function SavedPage() {
  const qc = useQueryClient();
  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
  });

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [overCol, setOverCol] = useState<SavedStatus | null>(null);

  const setStatus = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: SavedStatus }) =>
      endpoints.saved.setStatus(id, status),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ["saved"] });
      const prev = qc.getQueryData<{ items: SavedOpportunity[] }>(["saved"]);
      qc.setQueryData<{ items: SavedOpportunity[] } | undefined>(["saved"], (old) =>
        old
          ? {
              items: old.items.map((s) =>
                s.scholarship_id === id
                  ? { ...s, status, status_changed_at: new Date().toISOString() }
                  : s,
              ),
            }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["saved"], ctx?.prev);
      toast.error("Couldn't update status. Reverted.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => endpoints.saved.remove(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["saved"] });
      const prev = qc.getQueryData<{ items: SavedOpportunity[] }>(["saved"]);
      qc.setQueryData<{ items: SavedOpportunity[] } | undefined>(["saved"], (old) =>
        old ? { items: old.items.filter((s) => s.scholarship_id !== id) } : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["saved"], ctx?.prev);
      toast.error("Couldn't remove.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  function onDrop(status: SavedStatus) {
    if (!draggingId) return;
    const item = savedQ.data?.items.find((s) => s.scholarship_id === draggingId);
    if (item && item.status !== status) {
      setStatus.mutate({ id: draggingId, status });
    }
    setDraggingId(null);
    setOverCol(null);
  }

  if (savedQ.isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((c) => (
          <Skeleton key={c.status} className="h-96 w-full" />
        ))}
      </div>
    );
  }

  const items = savedQ.data?.items ?? [];

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-5">
        <h1 className="font-display text-3xl text-ink">Saved</h1>
        <p className="mt-1 text-ink-muted">
          Drag a card between columns to update status. {items.length} saved.
        </p>
      </header>

      {items.length === 0 ? (
        <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
          <h2 className="font-display text-xl text-ink">Nothing saved yet</h2>
          <p className="mt-2 text-ink-muted">
            Save a scholarship from your feed or discover to track it here.
          </p>
          <div className="mt-5">
            <Button asChild>
              <Link href="/discover">
                Browse all <ArrowRight className="size-4" strokeWidth={2} />
              </Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {COLUMNS.map((col) => {
            const colItems = items.filter((s) => s.status === col.status);
            return (
              <div
                key={col.status}
                onDragOver={(e) => {
                  e.preventDefault();
                  setOverCol(col.status);
                }}
                onDragLeave={() => setOverCol((c) => (c === col.status ? null : c))}
                onDrop={() => onDrop(col.status)}
                className={`rounded-[16px] border border-[var(--color-border)] bg-paper-warm/40 p-3 transition-colors duration-150 ${
                  overCol === col.status ? "ring-2 ring-[var(--color-ring)] bg-paper-warm" : ""
                }`}
              >
                <div className="mb-3 flex items-center justify-between gap-2 px-1">
                  <h2 className="font-display text-sm uppercase tracking-wider text-ink-muted">
                    {col.label}
                  </h2>
                  <Badge tone={col.tone}>{colItems.length}</Badge>
                </div>
                <div className="space-y-3">
                  {colItems.map((s) => (
                    <KanbanCard
                      key={s.scholarship_id}
                      saved={s}
                      dragging={draggingId === s.scholarship_id}
                      onDragStart={() => setDraggingId(s.scholarship_id)}
                      onDragEnd={() => {
                        setDraggingId(null);
                        setOverCol(null);
                      }}
                      onRemove={() => remove.mutate(s.scholarship_id)}
                    />
                  ))}
                  {colItems.length === 0 ? (
                    <p className="px-2 py-4 text-center text-xs text-ink-subtle">Empty</p>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function KanbanCard({
  saved,
  dragging,
  onDragStart,
  onDragEnd,
  onRemove,
}: {
  saved: SavedOpportunity;
  dragging: boolean;
  onDragStart: () => void;
  onDragEnd: () => void;
  onRemove: () => void;
}) {
  const s = saved.scholarship;
  const dl = s.deadline ? formatDeadline(s.deadline) : null;
  return (
    <Card
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={`cursor-grab active:cursor-grabbing ${
        dragging ? "opacity-50 ring-2 ring-[var(--color-ring)]" : ""
      }`}
    >
      <CardBody className="p-3">
        <div className="flex items-start gap-2">
          <GripVertical
            className="mt-1 size-4 shrink-0 text-ink-subtle"
            strokeWidth={2}
            aria-hidden
          />
          <div className="flex-1 min-w-0 space-y-2">
            <Link
              href={`/scholarships/${s.id}`}
              className="block font-display text-sm text-ink hover:underline underline-offset-4 line-clamp-2"
            >
              {s.title}
            </Link>
            <p className="truncate text-xs text-ink-muted">{s.provider}</p>
            {dl ? (
              <Badge
                tone={
                  dl.tone === "urgent"
                    ? "caution"
                    : dl.tone === "passed"
                      ? "danger"
                      : "neutral"
                }
              >
                {dl.label}
              </Badge>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove"
            className="rounded p-1 text-ink-subtle hover:bg-paper-warm hover:text-danger"
          >
            <Trash2 className="size-3.5" strokeWidth={2} />
          </button>
        </div>
      </CardBody>
    </Card>
  );
}
