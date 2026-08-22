"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { api, ApiError, type VerifyResult } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { VerificationChecks } from "@/components/VerificationChecks";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

export default function VerifyPage() {
  const params = useParams();
  const router = useRouter();
  const credentialId = String(params.credentialId ?? "");
  const [inputId, setInputId] = useState(credentialId === "demo" ? "" : credentialId);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(credentialId !== "demo");

  async function runVerify(id: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.verify(id);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Verification request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (credentialId && credentialId !== "demo") {
      runVerify(credentialId);
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [credentialId]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const id = inputId.trim();
    if (!id) return;
    router.push(`/verify/${encodeURIComponent(id)}`);
  }

  const verifyUrl =
    typeof window !== "undefined" && result?.found
      ? `${window.location.origin}/verify/${result.credential_id}`
      : "";

  return (
    <div className="container-ptn max-w-xl py-12">
      <PageHeader
        title="Verify a credential"
        subtitle="Public checks: issuer, signature, integrity, ledger proof, and revocation status."
      />

      <form onSubmit={onSubmit} className="card mb-6 space-y-3">
        <label className="label" htmlFor="credId">
          Credential ID
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            id="credId"
            className="input"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            placeholder="Enter credential ID"
          />
          <button type="submit" className="btn-primary shrink-0">
            Verify
          </button>
        </div>
      </form>

      {error && <ErrorBanner message={error} />}
      {loading && <LoadingBlock label="Running verification…" />}

      {result && !result.found && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600">
          Credential not found on the network.
        </div>
      )}

      {result?.found && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="font-serif text-xl font-semibold text-navy">{result.title}</h2>
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Type</dt>
                <dd className="text-right text-navy">{result.type}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Issuer</dt>
                <dd className="text-right text-navy">
                  {result.issuer?.name}
                  {result.issuer?.is_demo && (
                    <span className="ml-2 badge-pending">DEMO</span>
                  )}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Holder</dt>
                <dd className="text-right text-navy">{result.holder?.display_name}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Issued</dt>
                <dd className="text-right text-navy">{formatDate(result.issued_at)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Status</dt>
                <dd className="text-right text-navy">{result.status}</dd>
              </div>
            </dl>
          </div>

          <VerificationChecks checks={result.checks} overall={result.overall} />

          {verifyUrl && (
            <div className="card flex flex-col items-center gap-3 sm:flex-row sm:items-start">
              <QRCodeSVG value={verifyUrl} size={120} level="M" />
              <div className="text-center text-sm sm:text-left">
                <p className="font-medium text-navy">Share verification</p>
                <a href={verifyUrl} className="mt-1 break-all text-accent hover:underline">
                  {verifyUrl}
                </a>
              </div>
            </div>
          )}

          <p className="text-xs text-slate-500">
            Verification confirms cryptographic issuance and ledger anchoring. Not a government
            endorsement.
          </p>
        </div>
      )}
    </div>
  );
}
