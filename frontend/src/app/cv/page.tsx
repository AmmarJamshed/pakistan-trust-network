"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

type CvMe = Awaited<ReturnType<typeof api.cv.me>>;

export default function ManageCvPage() {
  const [cv, setCv] = useState<CvMe | null>(null);
  const [summary, setSummary] = useState("");
  const [visibility, setVisibility] = useState("PUBLIC");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    const data = await api.cv.me();
    setCv(data);
    setSummary(data.summary ?? "");
    setVisibility(data.visibility === "PRIVATE" ? "PUBLIC" : data.visibility);
  }

  useEffect(() => {
    (async () => {
      const user = await getCurrentUser();
      if (!user) {
        requireAuthRedirect();
        return;
      }
      try {
        await load();
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load CV");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function onPublish(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await api.cv.publish({ visibility, summary });
      setMessage(`Published. Public URL: ${res.public_url}`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Publish failed");
    } finally {
      setBusy(false);
    }
  }

  async function onUnpublish() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await api.cv.unpublish();
      setMessage("CV unpublished (private).");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Unpublish failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingBlock />;

  const grouped =
    cv?.items.reduce<Record<string, typeof cv.items>>((acc, item) => {
      (acc[item.section] ??= []).push(item);
      return acc;
    }, {}) ?? {};

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="PTN CV"
        subtitle="Sync from your wallet and publish a verifiable public profile."
        actions={
          cv?.public_url ? (
            <Link href={`/cv/${cv.username}`} className="btn-outline">
              View public CV
            </Link>
          ) : undefined
        }
      />
      {error && <ErrorBanner message={error} />}
      {message && (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-accent">
          {message}
        </div>
      )}

      <form onSubmit={onPublish} className="card mb-8 space-y-4">
        <div>
          <label className="label" htmlFor="summary">
            Summary
          </label>
          <textarea
            id="summary"
            className="input min-h-[88px]"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Short professional summary"
          />
        </div>
        <div>
          <label className="label" htmlFor="visibility">
            Visibility
          </label>
          <select
            id="visibility"
            className="input"
            value={visibility}
            onChange={(e) => setVisibility(e.target.value)}
          >
            <option value="PUBLIC">Public</option>
            <option value="LINK_ONLY">Link only</option>
          </select>
        </div>
        {cv && (
          <p className="text-sm text-navy-400">
            Username: <span className="font-medium text-navy">{cv.username}</span>
            {" · "}
            Status: <span className="font-medium text-navy">{cv.visibility}</span>
            {cv.public_url && (
              <>
                {" · "}
                <a href={cv.public_url} className="text-accent hover:underline">
                  {cv.public_url}
                </a>
              </>
            )}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Working…" : "Publish"}
          </button>
          <button type="button" className="btn-outline" disabled={busy} onClick={onUnpublish}>
            Unpublish
          </button>
        </div>
      </form>

      {!cv?.items.length ? (
        <EmptyState>No CV items yet. Credentials in your wallet will appear here after sync.</EmptyState>
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([section, items]) => (
            <section key={section}>
              <h2 className="font-serif text-xl font-semibold capitalize text-navy">{section}</h2>
              <ul className="mt-3 space-y-2">
                {items.map((item, idx) => (
                  <li key={`${item.title}-${idx}`} className="card flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-navy">{item.title}</p>
                      {item.subtitle && <p className="text-sm text-navy-400">{item.subtitle}</p>}
                    </div>
                    {item.credential_id ? (
                      <VerifiedBadge href={`/verify/${item.credential_id}`} />
                    ) : (
                      <VerifiedBadge />
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
