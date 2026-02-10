import type { TokenResponse, LoginCredentials, RegisterData, User } from "../types";

const BASE_URL = "/api";

async function authRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export function loginUser(credentials: LoginCredentials): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function registerUser(data: RegisterData): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function googleAuth(code: string): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function refreshTokenApi(refreshToken: string): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function logoutUser(refreshToken: string, accessToken: string): Promise<void> {
  return authRequest<void>("/auth/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function forgotPassword(email: string): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export function getProfile(accessToken: string): Promise<User> {
  return authRequest<User>("/users/me", {
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
  });
}

export function updateProfile(
  data: { nome?: string; email?: string },
  accessToken: string
): Promise<User> {
  return authRequest<User>("/users/me", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  });
}

export function changePassword(
  currentPassword: string,
  newPassword: string,
  accessToken: string
): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/users/me/password", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}
