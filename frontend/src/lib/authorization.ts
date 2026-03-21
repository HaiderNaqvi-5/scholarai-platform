import type { UserSession } from "@/lib/types";

export const Capability = {
  CurationQueueRead: "curation.queue.read",
  CurationRecordEdit: "curation.record.edit",
  CurationRecordTransition: "curation.record.transition",
  CurationImportWrite: "curation.import.write",
  CurationIngestionRun: "curation.ingestion.run",
  DocumentMentorReview: "document.mentor.review",
  DocumentMentorSubmit: "document.mentor.submit",
  AdminAuditRead: "admin.audit.read",
  OwnerSystemRead: "owner.system.read",
} as const;

type CapabilityValue = (typeof Capability)[keyof typeof Capability];

const ROLE_TO_CAPABILITIES: Record<string, Set<CapabilityValue>> = {
  student: new Set(),
  enduser_student: new Set(),
  university: new Set(),
  internal_user: new Set([
    Capability.CurationQueueRead,
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
    Capability.AdminAuditRead,
  ]),
  mentor: new Set([
    Capability.CurationQueueRead,
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
    Capability.AdminAuditRead,
  ]),
  dev: new Set([
    Capability.CurationQueueRead,
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
    Capability.AdminAuditRead,
  ]),
  admin: new Set([
    Capability.CurationQueueRead,
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
    Capability.AdminAuditRead,
  ]),
  owner: new Set([
    Capability.CurationQueueRead,
    Capability.DocumentMentorReview,
    Capability.DocumentMentorSubmit,
    Capability.AdminAuditRead,
    Capability.OwnerSystemRead,
  ]),
};

type TokenPayload = {
  capabilities?: unknown;
};

function decodePayload(token: string): TokenPayload | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padding = "=".repeat((4 - (base64.length % 4)) % 4);
    const decoded = atob(base64 + padding);
    return JSON.parse(decoded) as TokenPayload;
  } catch {
    return null;
  }
}

function getTokenCapabilities(token: string | null): Set<string> {
  if (!token) {
    return new Set();
  }

  const payload = decodePayload(token);
  if (!payload || !Array.isArray(payload.capabilities)) {
    return new Set();
  }

  return new Set(
    payload.capabilities.filter(
      (capability): capability is string =>
        typeof capability === "string" && capability.length > 0,
    ),
  );
}

export function hasCapability(
  user: UserSession | null,
  accessToken: string | null,
  capability: CapabilityValue,
): boolean {
  const tokenCapabilities = getTokenCapabilities(accessToken);
  if (tokenCapabilities.size > 0) {
    return tokenCapabilities.has(capability);
  }

  const role = user?.role?.toLowerCase() ?? "";
  return ROLE_TO_CAPABILITIES[role]?.has(capability) ?? false;
}

export function hasAnyCapability(
  user: UserSession | null,
  accessToken: string | null,
  capabilities: CapabilityValue[],
): boolean {
  return capabilities.some((capability) =>
    hasCapability(user, accessToken, capability),
  );
}
