"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

type Overview = Awaited<ReturnType<typeof api.admin.overview>>;

export default function AdminPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const user = await getCurrentUser();
      if (!user) {
        requireAuthRedirect();
        return;
      }
      try {
        setData(await api.admin.overview());
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.status === 403
              ? "Admin access required."
              : err.detail
            : "Failed to load admin overview"
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="Admin overview"
        subtitle="Network health, organizations, and recent audit events. Ledger history is append-only."
      />
      {error && <ErrorBanner message={error} />}
      {!data ? null : (
        <div className="space-y-10">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {Object.entries(data.stats).map(([k, v]) => (
              <div key={k} className="card">
                <p className="font-serif text-2xl font-semibold tabular-nums text-navy">
                  {Number(v).toLocaleString()}
                </p>
                <p className="mt-1 text-xs capitalize text-slate-500">{k.replace(/_/g, " ")}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card">
              <h2 className="font-serif text-lg font-semibold text-navy">Ledger chain</h2>
              <p className={`mt-2 text-sm ${data.chain.valid ? "text-accent" : "text-red-700"}`}>
                {data.chain.valid ? "✓ Valid" : "✗ Invalid"} · height {data.chain.height} · checked{" "}
                {data.chain.checked}
              </p>
            </div>
            <div className="card">
              <h2 className="font-serif text-lg font-semibold text-navy">Audit chain</h2>
              <p className={`mt-2 text-sm ${data.audit_chain.valid ? "text-accent" : "text-red-700"}`}>
                {data.audit_chain.valid ? "✓ Valid" : "✗ Invalid"}
                {data.audit_chain.count != null ? ` · ${data.audit_chain.count} entries` : ""}
              </p>
            </div>
          </div>

          <section>
            <h2 className="font-serif text-xl font-semibold text-navy">Organizations</h2>
            <ul className="mt-4 space-y-2">
              {data.organizations.map((o) => (
                <li key={o.id} className="card flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="font-medium text-navy">
                    {o.name}
                    {o.is_demo && <span className="ml-2 badge-pending">DEMO</span>}
                  </span>
                  <span className="badge-neutral">{o.status}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="font-serif text-xl font-semibold text-navy">Recent audit</h2>
            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Resource</th>
                    <th className="px-4 py-3">Time</th>
                    <th className="px-4 py-3">Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.audit_events.map((e, i) => (
                    <tr key={`${e.entry_hash}-${i}`}>
                      <td className="px-4 py-3 text-navy">{e.action}</td>
                      <td className="px-4 py-3 text-navy-400">{e.resource_id ?? "—"}</td>
                      <td className="px-4 py-3 text-navy-400">{formatDateTime(e.created_at)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{e.entry_hash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <p className="text-xs text-slate-500">{data.note}</p>
        </div>
      )}
    </div>
  );
}
