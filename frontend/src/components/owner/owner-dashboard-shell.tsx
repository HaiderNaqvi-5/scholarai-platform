"use client";

import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { FeedbackNotice } from "@/components/ui/feedback-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonLine } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuth } from "@/components/auth/auth-provider";
import { Capability, hasCapability } from "@/lib/authorization";
import {
  getAccessControlManagedUsers,
  getAccessControlRoleChanges,
  revertAccessControlRoleChange,
  updateAccessControlUserRole,
} from "@/lib/api";
import type {
  AccessControlManagedUser,
  AccessControlRoleChangeItem,
  ApiError,
} from "@/lib/types";

const ROLE_OPTIONS = [
  "enduser_student",
  "student",
  "mentor",
  "internal_user",
  "dev",
  "admin",
  "university",
  "owner",
] as const;

function getApiErrorMessage(error: unknown, fallback: string) {
  if (typeof error === "object" && error && "message" in error) {
    const maybeApiError = error as ApiError;
    if (typeof maybeApiError.message === "string" && maybeApiError.message) {
      return maybeApiError.message;
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function OwnerDashboardShell() {
  const { accessToken, currentUser } = useAuth();
  const canControlRoles = hasCapability(
    currentUser,
    accessToken,
    Capability.OwnerSystemControl,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [users, setUsers] = useState<AccessControlManagedUser[]>([]);
  const [roleChanges, setRoleChanges] = useState<AccessControlRoleChangeItem[]>([]);
  const [selectedTargetUserId, setSelectedTargetUserId] = useState<string>("");
  const [selectedRole, setSelectedRole] = useState<string>("mentor");
  const [updateReason, setUpdateReason] = useState("");
  const [revertReasonByAuditId, setRevertReasonByAuditId] = useState<Record<string, string>>(
    {},
  );
  const [actionFeedback, setActionFeedback] = useState<{
    message: string;
    variant: "error" | "success";
  } | null>(null);
  const [isUpdatingRole, setIsUpdatingRole] = useState(false);
  const [revertingAuditId, setRevertingAuditId] = useState<string | null>(null);

  const selectedUser = useMemo(
    () => users.find((user) => user.user_id === selectedTargetUserId) ?? null,
    [selectedTargetUserId, users],
  );

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;
    const load = async () => {
      setIsLoading(true);
      setActionFeedback(null);
      try {
        const [managedUsers, roleChangeList] = await Promise.all([
          getAccessControlManagedUsers(accessToken),
          getAccessControlRoleChanges(accessToken, { limit: 20 }),
        ]);
        if (!isActive) {
          return;
        }
        setUsers(managedUsers.items);
        setRoleChanges(roleChangeList.items);
        if (!selectedTargetUserId && managedUsers.items.length > 0) {
          setSelectedTargetUserId(managedUsers.items[0].user_id);
          setSelectedRole(managedUsers.items[0].role);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }
        setActionFeedback({
          message: getApiErrorMessage(error, "Unable to load owner access-control data."),
          variant: "error",
        });
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void load();
    return () => {
      isActive = false;
    };
  }, [accessToken, selectedTargetUserId]);

  const refreshRoleChanges = async () => {
    if (!accessToken) {
      return;
    }
    const roleChangeList = await getAccessControlRoleChanges(accessToken, { limit: 20 });
    setRoleChanges(roleChangeList.items);
  };

  const handleUpdateRole = async () => {
    if (!accessToken || !selectedTargetUserId) {
      return;
    }
    setIsUpdatingRole(true);
    setActionFeedback(null);
    try {
      const updated = await updateAccessControlUserRole(
        selectedTargetUserId,
        {
          role: selectedRole,
          reason: updateReason.trim() || null,
        },
        accessToken,
      );
      setUsers((current) =>
        current.map((user) =>
          user.user_id === selectedTargetUserId
            ? {
                ...user,
                role: updated.next_role,
              }
            : user,
        ),
      );
      setUpdateReason("");
      await refreshRoleChanges();
      setActionFeedback({ message: "Role updated and audit log recorded.", variant: "success" });
    } catch (error) {
      setActionFeedback({
        message: getApiErrorMessage(error, "Unable to update user role."),
        variant: "error",
      });
    } finally {
      setIsUpdatingRole(false);
    }
  };

  const handleRevertRoleChange = async (auditId: string) => {
    if (!accessToken) {
      return;
    }
    setRevertingAuditId(auditId);
    setActionFeedback(null);
    try {
      await revertAccessControlRoleChange(
        auditId,
        {
          reason: (revertReasonByAuditId[auditId] ?? "").trim() || null,
        },
        accessToken,
      );
      await refreshRoleChanges();
      setActionFeedback({ message: "Role change reverted and logged.", variant: "success" });
    } catch (error) {
      setActionFeedback({
        message: getApiErrorMessage(error, "Unable to revert role change."),
        variant: "error",
      });
    } finally {
      setRevertingAuditId(null);
    }
  };

  return (
    <AppShell
      eyebrow="Owner Home"
      title="Platform oversight and governance controls."
      description="Review system-level governance posture and navigate to owner-scoped controls."
    >
      <section className="metrics-grid" data-testid="owner-dashboard-shell">
        <article className="data-point">
          <p className="data-point__label">Stage conformance</p>
          <strong>v0.1 internal</strong>
          <p className="body-copy">Governance checks are available through admin analytics and audit surfaces.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Policy scope</p>
          <strong>Owner controls active</strong>
          <p className="body-copy">Owner role includes system-read oversight with elevated governance visibility.</p>
        </article>
        <article className="data-point">
          <p className="data-point__label">Role changes tracked</p>
          <strong>{roleChanges.length}</strong>
          <p className="body-copy">Recent permission updates with reversible audit records.</p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Governance"
            title="Platform governance pathways"
            description="Owner home centralizes stage conformance and policy oversight entry points."
          />
          <div className="surface-list">
            <article>
              <p className="list-heading">Admin analytics visibility</p>
              <p className="body-copy">
                Access aggregated operational metrics, ingestion health, and KPI trend snapshots from the Admin surface.
              </p>
            </article>
            <article>
              <p className="list-heading">Role and capability governance</p>
              <p className="body-copy">
                Monitor role-capability posture and ensure owner-only controls remain scoped to governance workflows.
              </p>
            </article>
          </div>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Trust boundary"
            title="Operational framing"
            description="Owner oversight tracks conformance and policy; user-facing scholarship facts remain sourced from published data."
          />
          <div className="meta-row">
            <StatusBadge label="Owner system read" variant="validated" />
            <StatusBadge label="Governance oversight" variant="generated" />
          </div>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="SLC-OPS-003"
            title="Role assignment controls"
            description="Assign roles with an auditable reason. Changes are tracked and can be reverted."
          />
          {!canControlRoles ? (
            <EmptyState
              title="Owner control required"
              description="Role updates and reversions are available only for owner-level control sessions."
            />
          ) : isLoading ? (
            <SkeletonLine count={3} />
          ) : users.length === 0 ? (
            <EmptyState
              title="No users available"
              description="Managed users will appear here once user records exist."
            />
          ) : (
            <div className="surface-list">
              <label className="form-field">
                <span className="form-field__label">Target user</span>
                <select
                  className="text-input"
                  value={selectedTargetUserId}
                  onChange={(event) => {
                    const nextUserId = event.target.value;
                    setSelectedTargetUserId(nextUserId);
                    const nextUser = users.find((user) => user.user_id === nextUserId);
                    if (nextUser) {
                      setSelectedRole(nextUser.role);
                    }
                  }}
                  disabled={isUpdatingRole}
                >
                  {users.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.full_name} ({user.email}) - {user.role}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-field">
                <span className="form-field__label">New role</span>
                <select
                  className="text-input"
                  value={selectedRole}
                  onChange={(event) => setSelectedRole(event.target.value)}
                  disabled={isUpdatingRole}
                >
                  {ROLE_OPTIONS.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-field">
                <span className="form-field__label">Reason (required for governance traceability)</span>
                <textarea
                  className="text-area"
                  value={updateReason}
                  onChange={(event) => setUpdateReason(event.target.value)}
                  rows={3}
                  disabled={isUpdatingRole}
                  placeholder="Explain why this role adjustment is required."
                />
              </label>
              <div className="meta-row">
                <StatusBadge
                  label={`Current role: ${selectedUser?.role ?? "unknown"}`}
                  variant="neutral"
                />
                <button
                  type="button"
                  className="auth-link auth-link--primary"
                  onClick={() => void handleUpdateRole()}
                  disabled={isUpdatingRole || !selectedTargetUserId || !selectedRole || !updateReason.trim()}
                >
                  {isUpdatingRole ? "Updating role..." : "Apply role update"}
                </button>
              </div>
            </div>
          )}
        </article>

        <article className="surface-card">
          <PageHeader
            eyebrow="Audit trail"
            title="Recent role changes"
            description="Review updates and revert reversible changes."
          />
          {!canControlRoles ? (
            <EmptyState
              title="Owner control required"
              description="Role change history is restricted to owner-level control sessions."
            />
          ) : isLoading ? (
            <SkeletonLine count={3} />
          ) : roleChanges.length === 0 ? (
            <EmptyState
              title="No role changes yet"
              description="Role update history will appear here after owner controls are used."
            />
          ) : (
            <div className="surface-list">
              {roleChanges.map((change) => (
                <article key={change.audit_id}>
                  <div className="meta-row">
                    <StatusBadge
                      label={`${change.previous_role} -> ${change.next_role}`}
                      variant="generated"
                    />
                    <span>{new Date(change.changed_at).toLocaleString()}</span>
                  </div>
                  <p className="list-heading">Target user: {change.target_user_id}</p>
                  <p className="body-copy">
                    Actor: {change.actor_user_id ?? "unknown"} | Reason: {change.reason ?? "n/a"}
                  </p>
                  <div className="form-field">
                    <span className="form-field__label">Revert reason</span>
                    <input
                      className="text-input"
                      type="text"
                      value={revertReasonByAuditId[change.audit_id] ?? ""}
                      onChange={(event) =>
                        setRevertReasonByAuditId((current) => ({
                          ...current,
                          [change.audit_id]: event.target.value,
                        }))
                      }
                      placeholder="Reason for rollback"
                      disabled={!change.is_reversible || revertingAuditId === change.audit_id}
                    />
                  </div>
                  <button
                    type="button"
                    className="auth-link auth-link--secondary"
                    onClick={() => void handleRevertRoleChange(change.audit_id)}
                    disabled={!change.is_reversible || revertingAuditId === change.audit_id}
                  >
                    {revertingAuditId === change.audit_id
                      ? "Reverting..."
                      : change.is_reversible
                        ? "Revert change"
                        : "Already reverted"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </article>
      </section>

      {actionFeedback ? (
        <FeedbackNotice message={actionFeedback.message} variant={actionFeedback.variant} />
      ) : null}

      <section className="surface-band">
        <p className="body-copy">
          Signed in as <strong>{currentUser?.full_name ?? "Owner"}</strong>. Owner role updates
          invalidate prior tokens by incrementing auth token version.
        </p>
      </section>
    </AppShell>
  );
}
