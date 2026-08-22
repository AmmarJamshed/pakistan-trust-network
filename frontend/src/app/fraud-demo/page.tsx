"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { VerificationChecks } from "@/components/VerificationChecks";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

type TamperResult = Awaited<ReturnType<typeof api.credentials.tamperCheck>>;

export default function FraudDemoPage() {
  const [credentialId, setCredentialId] = useState("");
  const [modifiedJson, setModifiedJson] = useState(
    '{\n  "degree": "PhD Fake Studies",\n  "program": "Tampered Program"\n}'
  );
  const [result, setResult] = useState<TamperResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getCurrentUser().then((u) => {
      if (!u) {
        requireAuthRedirect();
        return;
      }
      setLoading(false);
    });
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    let modified: Record<string, unknown>;
    try {
      modified = JSON.parse(modifiedJson);
    } catch {
      setError("Modified subject must be valid JSON");
      setBusy(false);
      return;
    }
    try {
      const data = await api.credentials.tamperCheck({
        credential_id: credentialId.trim(),
        modified_subject: modified,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Demo request failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn max-w-3xl py-12">
      <PageHeader
        title="Fraud / integrity demo"
        subtitle="Compare an original credential verification against a deliberately modified subject payload. Simulation only."
      />

      <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        DEMO / SIMULATION — This endpoint demonstrates that changing credential content fails
        integrity checks. It does not forge credentials or alter the ledger.
      </div>

      {error && <ErrorBanner message={error} />}

      <form onSubmit={onSubmit} className="card mb-8 space-y-4">
        <div>
          <label className="label" htmlFor="cid">
            Credential ID
          </label>
          <input
            id="cid"
            className="input"
            required
            value={credentialId}
            onChange={(e) => setCredentialId(e.target.value)}
            placeholder="Paste an existing credential id"
          />
        </div>
        <div>
          <label className="label" htmlFor="mod">
            Modified subject (JSON)
          </label>
          <textarea
            id="mod"
            className="input min-h-[140px] font-mono text-xs"
            value={modifiedJson}
            onChange={(e) => setModifiedJson(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy ? "Running…" : "Run tamper check"}
        </button>
      </form>

      {result && (
        <div className="space-y-8">
          <p className="text-xs text-slate-500">{result.disclaimer}</p>
          <div className="grid gap-8 md:grid-cols-2">
            <div>
              <h2 className="mb-3 font-serif text-lg font-semibold text-accent">
                Original · {result.original.overall}
              </h2>
              <VerificationChecks
                checks={result.original.checks}
                overall={result.original.overall}
              />
            </div>
            <div>
              <h2 className="mb-3 font-serif text-lg font-semibold text-red-700">
                Modified · {result.modified.overall}
              </h2>
              <VerificationChecks
                checks={result.modified.checks}
                overall={result.modified.overall}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
