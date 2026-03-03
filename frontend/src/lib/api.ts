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

export interface ProfileResponse {
  id: string;
  user_id: string;
  net_monthly_income: number | null;
  pay_frequency: string | null;
  fixed_expenses: Record<string, number>;
  debts: Array<{
    name: string;
    balance: number;
    rate: number;
    minimum: number;
  }>;
  budget_targets: Record<string, number>;
  family_support_recipients: string[];
  emergency_fund: number;
  risk_tolerance: string;
  onboarding_complete: boolean;
}

export interface OnboardingResponse {
  reply: string;
  profile_update: Record<string, unknown> | null;
  onboarding_complete: boolean;
}

export const profileApi = {
  get: () => api.get<ProfileResponse>("/profile"),
  update: (data: Partial<ProfileResponse>) =>
    api.put<ProfileResponse>("/profile", data),
  completeOnboarding: () =>
    api.post<ProfileResponse>("/profile/onboarding-complete"),
};

export const onboardingApi = {
  chat: (message: string, history: Array<{ role: string; content: string }>) =>
    api.post<OnboardingResponse>("/onboarding/chat", { message, history }),
};

export const authApi = {
  register: (email: string, password: string) =>
    api.post<UserResponse>("/auth/register", { email, password }),
  login: (email: string, password: string) =>
    api.post<UserResponse>("/auth/login", { email, password }),
  me: () => api.get<UserResponse>("/auth/me"),
  logout: () => api.post<void>("/auth/logout"),
};
