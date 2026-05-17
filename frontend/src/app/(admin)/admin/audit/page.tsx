"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/section-header";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { endpoints } from "@/lib/api";
import type { RoleChangeAudit } from "@/lib/api";

export default function AdminAuditPage() {
  const auditsQ = useQuery({
    queryKey: ["access-control", "role-changes"],
    queryFn: () => endpoints.accessControl.listRoleChanges({ limit: 100 }),
  });

  const [target, setTarget] = useState<RoleChangeAudit | null>(null);

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Role-change audit"
        description="Every role mutation. Owners can revert with a reason."
      />

      {auditsQ.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : !auditsQ.data || auditsQ.data.items.length === 0 ? (
        <p className="text-ink-subtle">No role changes recorded.</p>
      ) : (
        <div className="overflow-hidden rounded-[16px] border border-[var(--color-border)] bg-paper-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[var(--color-border)] bg-paper-warm/40 text-left text-xs uppercase tracking-wider text-ink-subtle">
              <tr>
                <th className="px-3 py-2">When</th>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Change</th>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Reason</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {auditsQ.data.items.map((a) => (
                <tr
                  key={a.audit_id}
                  className="border-b border-[var(--color-border)] last:border-b-0 hover:bg-paper-warm/30"
                >
                  <td className="px-3 py-2 font-mono text-xs text-ink-muted">
                    {new Date(a.changed_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-ink">{a.target_user_id}</td>
                  <td className="px-3 py-2">
                    <span className="inline-flex items-center gap-1.5 text-ink">
                      <Badge tone="neutral">{a.from_role}</Badge>
                      <span className="text-ink-subtle">→</span>
                      <Badge tone="validated">{a.to_role}</Badge>
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-ink-muted">{a.actor_user_id}</td>
                  <td className="px-3 py-2 text-ink">{a.reason}</td>
                  <td className="px-3 py-2 text-right">
                    {a.reverted_audit_id ? (
                      <Badge tone="caution">reverted</Badge>
                    ) : (
                      <Button size="sm" variant="secondary" onClick={() => setTarget(a)}>
                        <RotateCcw className="size-4" strokeWidth={2} /> Revert
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <RevertModal audit={target} onClose={() => setTarget(null)} />
    </div>
  );
}

function RevertModal({
  audit,
  onClose,
}: {
  audit: RoleChangeAudit | null;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [reason, setReason] = useState("");

  const mut = useMutation({
    mutationFn: () => endpoints.accessControl.revertChange(audit!.audit_id, reason.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["access-control"] });
      toast.success("Reverted.");
      onClose();
    },
    onError: () => toast.error("Couldn't revert."),
  });

  return (
    <Dialog
      open={!!audit}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent onOpenAutoFocus={() => setReason("")}>
        <DialogHeader>
          <DialogTitle>Revert role change</DialogTitle>
          <DialogDescription>
            {audit
              ? `Will set role back from ${audit.to_role} to ${audit.from_role}.`
              : ""}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (reason.trim().length < 5) {
              toast.error("Need a reason (5+ chars).");
              return;
            }
            mut.mutate();
          }}
          className="mt-4 space-y-3"
        >
          <div className="space-y-2">
            <Label htmlFor="reason">Reason (audited)</Label>
            <Input
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why revert?"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" loading={mut.isPending}>
              Revert
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
