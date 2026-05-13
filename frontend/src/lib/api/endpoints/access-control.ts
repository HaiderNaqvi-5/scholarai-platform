import { api } from "../client";
import type { Role, RoleChangeAudit, User } from "../types";

export const accessControl = {
  listUsers: () =>
    api.get<{ items: (User & { current_role: Role })[] }>("/access-control/users"),

  listRoleChanges: (filters: { target_user_id?: string; limit?: number } = {}) =>
    api.get<{ items: RoleChangeAudit[] }>("/access-control/role-changes", { query: filters }),

  updateRole: (userId: string, input: { role: Role; reason: string }) =>
    api.patch<RoleChangeAudit>(`/access-control/users/${userId}/role`, input),

  revertChange: (auditId: string, reason: string) =>
    api.post<RoleChangeAudit>(`/access-control/role-changes/${auditId}/revert`, { reason }),
};
