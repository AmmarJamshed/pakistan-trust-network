function resolveApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (raw === "same-origin") {
    return "";
  }
  if (!raw) {
    return "http://localhost:8000";
  }
  return raw.replace(/\/$/, "");
}

/** Empty string means same-origin (Docker / reverse proxy). */
export const API_BASE = resolveApiBase();

const ACCESS_KEY = "ptn_access_token";
const REFRESH_KEY = "ptn_refresh_token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function apiDocsUrl(): string {
  return `${API_BASE}/api/docs`;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : Array.isArray(body.detail)
            ? body.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ")
            : JSON.stringify(body.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  username: string | null;
  did: string;
  role: string;
  headline?: string | null;
  country?: string | null;
  is_demo?: boolean;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  org_type: string;
  country: string;
  website: string | null;
  email: string;
  description: string | null;
  status: string;
  did: string;
  is_demo: boolean;
  demo_label?: string | null;
  has_identity?: boolean;
};

export type Credential = {
  credential_id: string;
  type_code: string;
  title: string;
  issuer_name?: string | null;
  issuer_did?: string | null;
  holder_did?: string | null;
  issued_at: string;
  status: string;
  credential_hash: string;
  ledger_tx_id?: string | null;
  is_demo?: boolean;
  verification_url?: string | null;
};

export type Stats = {
  organizations: number;
  credentials_issued: number;
  credentials_verified: number;
  blocks: number;
  transactions: number;
  active_credentials: number;
};

export type VerifyResult = {
  found: boolean;
  credential_id: string;
  overall: string;
  title?: string;
  type?: string;
  issuer?: {
    name: string;
    did: string;
    is_demo?: boolean;
    demo_label?: string | null;
    status?: string;
  };
  holder?: { display_name: string; did?: string };
  issued_at?: string;
  status?: string;
  checks: Record<string, boolean>;
  public_subject?: Record<string, unknown>;
  revocation?: { revoked_at?: string; issuer?: string; reason?: string | null } | null;
  ledger_tx_id?: string | null;
  credential_hash?: string;
  disclaimer?: string;
};

export type WalletCredential = {
  credential_id: string;
  title: string;
  type: string;
  issuer: string;
  issuer_did: string;
  issued_at: string;
  status: string;
  verified: boolean;
  credential_hash: string;
  ledger_tx_id: string | null;
  verification_url: string;
  is_demo: boolean;
};

export type Wallet = {
  holder: { full_name: string; did: string; username: string | null };
  categories: Record<string, WalletCredential[]>;
  count: number;
};

export type LedgerBlock = {
  index: number;
  timestamp: string;
  previous_hash: string;
  merkle_root: string;
  validator: string;
  block_hash: string;
  transaction_count: number;
};

export const api = {
  auth: {
    register: (body: {
      email: string;
      password: string;
      full_name: string;
      username?: string;
      account_type?: string;
    }) =>
      request<TokenResponse>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    login: (body: { email: string; password: string }) =>
      request<TokenResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    me: () => request<User>("/api/auth/me", {}, true),
    refresh: (refresh_token: string) =>
      request<TokenResponse>("/api/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token }),
      }),
  },

  organizations: {
    create: (body: {
      name: string;
      org_type: string;
      country?: string;
      website?: string;
      email: string;
      description?: string;
    }) =>
      request<Organization>("/api/organizations", {
        method: "POST",
        body: JSON.stringify(body),
      }, true),
    list: (params?: { status_filter?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.status_filter) q.set("status_filter", params.status_filter);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<Organization[]>(`/api/organizations${qs ? `?${qs}` : ""}`);
    },
    mine: () => request<Organization[]>("/api/organizations/mine", {}, true),
    get: (id: string) => request<Organization>(`/api/organizations/${id}`),
  },

  credentials: {
    issue: (body: {
      organization_id: string;
      holder_email?: string;
      holder_did?: string;
      type_code: string;
      title: string;
      credential_subject?: Record<string, unknown>;
      public_fields?: string[];
    }) =>
      request<Credential>("/api/credentials", {
        method: "POST",
        body: JSON.stringify(body),
      }, true),
    revoke: (credentialId: string, body?: { reason?: string; public_reason?: boolean }) =>
      request<Credential>(`/api/credentials/${credentialId}/revoke`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }, true),
    list: (organizationId: string) =>
      request<Credential[]>(`/api/credentials/issued/${organizationId}`, {}, true),
    get: (credentialId: string) =>
      request<Credential>(`/api/credentials/${credentialId}`, {}, true),
    tamperCheck: (body: {
      credential_id: string;
      modified_subject: Record<string, unknown>;
    }) =>
      request<{
        disclaimer: string;
        original: { overall: string; checks: Record<string, boolean> };
        modified: { overall: string; checks: Record<string, boolean> };
      }>("/api/credentials/demo/tamper-check", {
        method: "POST",
        body: JSON.stringify(body),
      }, true),
  },

  verify: (credentialId: string) =>
    request<VerifyResult>(`/api/verify/${encodeURIComponent(credentialId)}`),

  wallet: {
    me: () => request<Wallet>("/api/wallet/me", {}, true),
  },

  cv: {
    me: () =>
      request<{
        username: string;
        visibility: string;
        summary: string | null;
        share_token: string | null;
        public_url: string | null;
        items: { section: string; title: string; subtitle: string | null; credential_id: string | null }[];
      }>("/api/cv/me", {}, true),
    publish: (body: { visibility?: string; summary?: string }) =>
      request<{
        username: string;
        visibility: string;
        public_url: string;
        share_token: string | null;
        qr_target: string;
      }>("/api/cv/publish", {
        method: "POST",
        body: JSON.stringify(body),
      }, true),
    unpublish: () =>
      request<{ username: string; visibility: string }>("/api/cv/unpublish", {
        method: "POST",
      }, true),
    public: (username: string, token?: string) => {
      const qs = token ? `?token=${encodeURIComponent(token)}` : "";
      return request<{
        username: string;
        full_name: string;
        headline: string | null;
        summary: string | null;
        visibility: string;
        published_at: string | null;
        sections: Record<
          string,
          {
            title: string;
            subtitle: string | null;
            verified: boolean;
            credential_id: string | null;
            status: string | null;
          }[]
        >;
        disclaimer: string;
      }>(`/api/cv/${encodeURIComponent(username)}${qs}`);
    },
  },

  ledger: {
    blocks: (limit = 20, offset = 0) =>
      request<{ height: number; blocks: LedgerBlock[] }>(
        `/api/ledger/blocks?limit=${limit}&offset=${offset}`
      ),
    block: (height: number) =>
      request<LedgerBlock & { transactions?: unknown[] }>(`/api/ledger/blocks/${height}`),
    search: (q: string) =>
      request<{
        blocks: LedgerBlock[];
        transactions: {
          transaction_id: string;
          transaction_type: string;
          credential_id: string | null;
          credential_hash: string | null;
          timestamp: string;
          block_index: number | null;
        }[];
      }>(`/api/ledger/search?q=${encodeURIComponent(q)}`),
    verifyChain: () =>
      request<{ valid: boolean; height: number; checked: number; errors?: string[] }>(
        "/api/ledger/verify-chain"
      ),
  },

  stats: () => request<Stats>("/api/stats"),

  network: {
    status: () =>
      request<{
        enabled: boolean;
        repo_root: string | null;
        git_bash: string | null;
        remote: string;
        branch: string;
        can_push: boolean;
        interval_seconds: number;
        last_sync: string | null;
        last_error: string | null;
        last_result: Record<string, unknown> | null;
        running: boolean;
      }>("/api/network/status"),
    sync: () => request<Record<string, unknown>>("/api/network/sync", { method: "POST" }),
  },

  admin: {
    overview: () =>
      request<{
        stats: Stats;
        chain: { valid: boolean; height: number; checked: number; errors?: string[] };
        audit_chain: { valid: boolean; count?: number };
        organizations: { id: string; name: string; status: string; is_demo: boolean; did: string }[];
        audit_events: {
          action: string;
          actor_id: string | null;
          resource_id: string | null;
          created_at: string;
          entry_hash: string;
        }[];
        note: string;
      }>("/api/admin/overview", {}, true),
  },
};
