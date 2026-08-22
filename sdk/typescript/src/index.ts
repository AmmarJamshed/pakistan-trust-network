/**
 * Pakistan Trust Network — TypeScript SDK (browser / Node).
 */
export type PTNOptions = {
  apiUrl?: string;
  token?: string;
};

export class PTN {
  apiUrl: string;
  token?: string;

  constructor(opts: PTNOptions = {}) {
    this.apiUrl = (opts.apiUrl || "http://localhost:8000").replace(/\/$/, "");
    this.token = opts.token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    auth = true
  ): Promise<T> {
    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
    };
    if (auth && this.token) headers.Authorization = `Bearer ${this.token}`;
    const res = await fetch(`${this.apiUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`PTN API ${res.status}: ${err}`);
    }
    return res.json() as Promise<T>;
  }

  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string }>(
      "POST",
      "/api/auth/login",
      { email, password },
      false
    );
    this.token = data.access_token;
    return data;
  }

  verify(credentialId: string) {
    return this.request("GET", `/api/verify/${encodeURIComponent(credentialId)}`, undefined, false);
  }

  issueCredential(payload: {
    organization_id: string;
    holder_email?: string;
    holder_did?: string;
    type_code: string;
    title: string;
    credential_subject?: Record<string, unknown>;
  }) {
    return this.request("POST", "/api/credentials", payload);
  }

  wallet() {
    return this.request("GET", "/api/wallet/me");
  }

  stats() {
    return this.request("GET", "/api/stats", undefined, false);
  }
}

export default PTN;
