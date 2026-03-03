const API_BASE = "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(error.detail || "Request failed", res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface UserResponse {
  id: string;
  email: string;
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: "PUT", body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
};

export const authApi = {
  register: (email: string, password: string) =>
    api.post<UserResponse>("/auth/register", { email, password }),
  login: (email: string, password: string) =>
    api.post<UserResponse>("/auth/login", { email, password }),
  me: () => api.get<UserResponse>("/auth/me"),
  logout: () => api.post<void>("/auth/logout"),
};
