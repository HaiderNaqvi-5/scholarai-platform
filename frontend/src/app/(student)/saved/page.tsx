"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { stageLabel } from "@/lib/tracker/stages";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bookmark } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { PageHeader } from "@/components/ui/section-header";
import { SavedRow } from "@/components/saved/SavedRow";
import { SortDropdown, type SavedSort } from "@/components/saved/SortDropdown";
import { endpoints, isPlanRequiredError } from "@/lib/api";
import type { SavedOpportunity } from "@/lib/api/types";

/**
 * /saved — Front-upgrade §6.11.
 *
 * Single ordered list with sort (Recently saved | Deadline). No Kanban —
 * status workflow lives on /tracker. Inline Promote (POST /tracker) +
 * Remove (DELETE /saved-opportunities/{id}) with optimistic updates and
 * rollback toasts.
 */
export default function SavedPage() {
  const qc = useQueryClient();
  const [sort, setSort] = useState<SavedSort>("recent");

  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
  });

  const promote = useMutation({
    mutationFn: async (item: SavedOpportunity) => {
      await endpoints.tracker.create({
        scholarship_id: item.scholarship_id,
        program_name: item.scholarship.title,
        university_name: item.scholarship.provider,
        deadline: item.scholarship.deadline ?? null,
        stage: "researching",
      });
      await endpoints.saved.remove(item.scholarship_id);
      return item;
    },
    onMutate: async (item) => {
      await qc.cancelQueries({ queryKey: ["saved"] });
      const prev = qc.getQueryData<{ items: SavedOpportunity[] }>(["saved"]);
      qc.setQueryData<{ items: SavedOpportunity[] } | undefined>(["saved"], (old) =>
        old ? { items: old.items.filter((s) => s.scholarship_id !== item.scholarship_id) } : old,
      );
      return { prev };
    },
    onError: (err, _v, ctx) => {
      qc.setQueryData(["saved"], ctx?.prev);
      if (isPlanRequiredError(err)) {
        toast.error(err.detail.message);
      } else {
        toast.error("Couldn't move to tracker. Restored.");
      }
    },
    onSuccess: () => {
      toast.success(`Moved to ${stageLabel("researching")} in tracker.`);
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
      toast.error("Couldn't remove. Restored.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  const items = useMemo(() => savedQ.data?.items ?? [], [savedQ.data]);
  const sorted = useMemo(() => {
    const arr = [...items];
    if (sort === "deadline") {
      arr.sort((a, b) => {
        const ad = a.scholarship.deadline ? new Date(a.scholarship.deadline).getTime() : Infinity;
        const bd = b.scholarship.deadline ? new Date(b.scholarship.deadline).getTime() : Infinity;
        return ad - bd;
      });
    } else {
      arr.sort((a, b) => new Date(b.saved_at).getTime() - new Date(a.saved_at).getTime());
    }
    return arr;
  }, [items, sort]);

  return (
    <div className="mx-auto max-w-[1024px]">
      <PageHeader
        title="Saved"
        description={
          items.length > 0
            ? `${items.length} scholarship${items.length === 1 ? "" : "s"} bookmarked.`
            : undefined
        }
        actions={items.length > 0 ? <SortDropdown value={sort} onChange={setSort} /> : undefined}
      />

      <section className="mt-6">
        {savedQ.isLoading ? (
          <ul className="space-y-3" aria-busy>
            {Array.from({ length: 4 }).map((_, i) => (
              <li key={i}>
                <Skeleton className="h-[112px] w-full rounded-[18px]" />
              </li>
            ))}
          </ul>
        ) : savedQ.isError ? (
          <ErrorState
            title="Couldn't load your saved list."
            description="Check your connection, then retry."
            action={<Button onClick={() => savedQ.refetch()}>Retry</Button>}
          />
        ) : sorted.length === 0 ? (
          <EmptyState
            icon={<Bookmark className="size-8" strokeWidth={1.5} />}
            title="Nothing saved yet."
            description="Use the save icon on any scholarship to bookmark it for later."
            action={
              <Button asChild>
                <Link href="/discover">Browse scholarships</Link>
              </Button>
            }
          />
        ) : (
          <ul data-testid="saved-list" className="space-y-3">
            {sorted.map((s) => (
              <SavedRow
                key={s.scholarship_id}
                saved={s}
                onPromote={() => promote.mutate(s)}
                onRemove={() => remove.mutate(s.scholarship_id)}
                promoting={promote.isPending && promote.variables?.scholarship_id === s.scholarship_id}
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
