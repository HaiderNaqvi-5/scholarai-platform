import type { ApiError } from "@/lib/types";

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
