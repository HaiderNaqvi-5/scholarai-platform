import type {
  AccessControlManagedUserListResponse,
  AccessControlRoleChangeItem,
  AccessControlRoleChangeListResponse,
  AccessControlRoleRevertRequest,
  AccessControlRoleUpdateRequest,
  ApiError,
  DocumentListResponse,
  DocumentDetail,
  MentorFeedbackRequest,
  MentorFeedbackResponse,
  PlatformAnalyticsResponse,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type RequestOptions = RequestInit & {
  token?: string | null;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { token, headers, ...init } = options;
  const isFormData =
    typeof FormData !== "undefined" && init.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function parseError(response: Response): Promise<ApiError> {
  let message = response.statusText || "Unexpected API failure";

  try {
    const payload = (await response.json()) as {
      detail?: string | Array<{ msg?: string }>;
      error?: {
        code?: string;
        message?: string;
        request_id?: string;
        status?: number;
      };
    };
    if (payload.error?.message) {
      message = payload.error.message;
      return {
        code: payload.error.code ?? `HTTP_${response.status}`,
        message,
        request_id: payload.error.request_id,
        status: payload.error.status ?? response.status,
      };
    } else if (typeof payload.detail === "string") {
      message = payload.detail;
    } else if (Array.isArray(payload.detail) && payload.detail.length > 0) {
      message = payload.detail[0]?.msg || message;
    }
  } catch {
    message = response.statusText || "Unexpected API failure";
  }

  return {
    code: `HTTP_${response.status}`,
    message,
    status: response.status,
  };
}

export async function getMentorPendingReviews(token?: string | null) {
  return apiRequest<DocumentListResponse>("/mentor/pending-reviews", { token });
}

export async function getMentorDocument(documentId: string, token?: string | null) {
  return apiRequest<DocumentDetail>(`/mentor/documents/${documentId}`, { token });
}

export async function submitMentorFeedback(
  documentId: string,
  feedback: MentorFeedbackRequest,
  token?: string | null,
) {
  return apiRequest<MentorFeedbackResponse>(
    `/mentor/documents/${documentId}/feedback`,
    {
      method: "POST",
      body: JSON.stringify(feedback),
      token,
    },
  );
}

export async function getAdminAnalytics(token?: string | null) {
  return apiRequest<PlatformAnalyticsResponse>("/analytics", { token });
}

export async function getAccessControlManagedUsers(token?: string | null) {
  return apiRequest<AccessControlManagedUserListResponse>("/access-control/users", {
    token,
  });
}

export async function getAccessControlRoleChanges(
  token?: string | null,
  options?: {
    target_user_id?: string;
    limit?: number;
  },
) {
  const search = new URLSearchParams();
  if (options?.target_user_id) {
    search.set("target_user_id", options.target_user_id);
  }
  if (typeof options?.limit === "number") {
    search.set("limit", String(options.limit));
  }
  const query = search.toString();
  const path = query
    ? `/access-control/role-changes?${query}`
    : "/access-control/role-changes";
  return apiRequest<AccessControlRoleChangeListResponse>(path, { token });
}

export async function updateAccessControlUserRole(
  targetUserId: string,
  payload: AccessControlRoleUpdateRequest,
  token?: string | null,
) {
  return apiRequest<AccessControlRoleChangeItem>(
    `/access-control/users/${targetUserId}/role`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      token,
    },
  );
}

export async function revertAccessControlRoleChange(
  auditId: string,
  payload: AccessControlRoleRevertRequest,
  token?: string | null,
) {
  return apiRequest<AccessControlRoleChangeItem>(
    `/access-control/role-changes/${auditId}/revert`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      token,
    },
  );
}
