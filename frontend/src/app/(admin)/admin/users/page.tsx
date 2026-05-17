"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shield } from "lucide-react";
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
import type { Role, User } from "@/lib/api";

const ROLES: Role[] = [
  "enduser_student",
  "student",
  "internal_user",
  "mentor",
  "dev",
  "admin",
  "owner",
  "university",
];

export default function AdminUsersPage() {
  const usersQ = useQuery({
    queryKey: ["access-control", "users"],
    queryFn: endpoints.accessControl.listUsers,
  });

  const [target, setTarget] = useState<(User & { current_role: Role }) | null>(null);

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Users"
        description="Roster and current role. Owners can mutate role with a reason."
      />
      <header className="sr-only">
        <p>
          Roster and current role. Owners can mutate role with a reason.
        </p>
      </header>

      {usersQ.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : !usersQ.data || usersQ.data.items.length === 0 ? (
        <p className="text-ink-subtle">No users.</p>
      ) : (
        <div className="overflow-hidden rounded-[16px] border border-[var(--color-border)] bg-paper-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[var(--color-border)] bg-paper-warm/40 text-left text-xs uppercase tracking-wider text-ink-subtle">
              <tr>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {usersQ.data.items.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-[var(--color-border)] last:border-b-0 hover:bg-paper-warm/30"
                >
                  <td className="px-3 py-2 text-ink">{u.email}</td>
                  <td className="px-3 py-2 text-ink-muted">{u.full_name ?? "—"}</td>
                  <td className="px-3 py-2">
                    <Badge tone={u.current_role === "owner" ? "validated" : "neutral"}>
                      {u.current_role}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button size="sm" variant="secondary" onClick={() => setTarget(u)}>
                      <Shield className="size-4" strokeWidth={2} /> Change role
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <RoleModal user={target} onClose={() => setTarget(null)} />
    </div>
  );
}

function RoleModal({
  user,
  onClose,
}: {
  user: (User & { current_role: Role }) | null;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [role, setRole] = useState<Role>(user?.current_role ?? "enduser_student");
  const [reason, setReason] = useState("");

  const mut = useMutation({
    mutationFn: () =>
      endpoints.accessControl.updateRole(user!.id, { role, reason: reason.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["access-control"] });
      toast.success("Role updated.");
      onClose();
    },
    onError: () => toast.error("Couldn't update role."),
  });

  const valid = !!user && role !== user.current_role && reason.trim().length > 5;

  return (
    <Dialog
      open={!!user}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent
        onOpenAutoFocus={() => {
          if (user) setRole(user.current_role);
          setReason("");
        }}
      >
        <DialogHeader>
          <DialogTitle>Change role</DialogTitle>
          <DialogDescription>{user?.email}</DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!valid) {
              toast.error("Pick a different role and explain why (5+ chars).");
              return;
            }
            mut.mutate();
          }}
          className="mt-4 space-y-3"
        >
          <div className="space-y-2">
            <Label htmlFor="role">New role</Label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="reason">Reason (audited)</Label>
            <Input
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why this change?"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mut.isPending} disabled={!valid}>
              Confirm
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
