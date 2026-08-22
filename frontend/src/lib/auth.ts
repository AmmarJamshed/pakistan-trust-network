"use client";

import { api, clearTokens, getRefreshToken, setTokens, type User } from "./api";

export async function loginAndStore(email: string, password: string): Promise<User> {
  const tokens = await api.auth.login({ email, password });
  setTokens(tokens.access_token, tokens.refresh_token);
  return api.auth.me();
}

export async function registerAndStore(payload: {
  email: string;
  password: string;
  full_name: string;
  username?: string;
  account_type?: string;
}): Promise<User> {
  const tokens = await api.auth.register(payload);
  setTokens(tokens.access_token, tokens.refresh_token);
  return api.auth.me();
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    return await api.auth.me();
  } catch {
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      return null;
    }
    try {
      const tokens = await api.auth.refresh(refresh);
      setTokens(tokens.access_token, tokens.refresh_token);
      return await api.auth.me();
    } catch {
      clearTokens();
      return null;
    }
  }
}

export function logout() {
  clearTokens();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export function requireAuthRedirect() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}
