"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError, type LedgerBlock } from "@/lib/api";
import { formatDateTime, truncateHash } from "@/lib/format";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

export default function ExplorerPage() {
  const [blocks, setBlocks] = useState<LedgerBlock[]>([]);
  const [height, setHeight] = useState(0);
  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState<{
    blocks: LedgerBlock[];
    transactions: {
      transaction_id: string;
      transaction_type: string;
      credential_id: string | null;
      timestamp: string;
      block_index: number | null;
    }[];
  } | null>(null);
  const [chain, setChain] = useState<{
    valid: boolean;
    height: number;
    checked: number;
    errors?: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    api.ledger
      .blocks(25)
      .then((res) => {
        setBlocks(res.blocks);
        setHeight(res.height);
      })
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Failed to load blocks"))
      .finally(() => setLoading(false));
  }, []);

  async function onSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setError(null);
    try {
      setSearchResult(await api.ledger.search(query.trim()));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Search failed");
    }
  }

  async function onVerifyChain() {
    setVerifying(true);
    setError(null);
    try {
      setChain(await api.ledger.verifyChain());
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Chain verification failed");
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="Ledger explorer"
        subtitle={`Browse anchored blocks and verify chain integrity. Current height: ${height}`}
        actions={
          <button type="button" className="btn-accent" onClick={onVerifyChain} disabled={verifying}>
            {verifying ? "Checking…" : "Verify chain integrity"}
          </button>
        }
      />

      {error && <ErrorBanner message={error} />}

      {chain && (
        <div
          className={`mb-6 rounded-lg border px-4 py-3 text-sm ${
            chain.valid
              ? "border-emerald-200 bg-emerald-50 text-accent"
              : "border-red-200 bg-red-50 text-red-800"
          }`}
        >
          Chain {chain.valid ? "VALID" : "INVALID"} · checked {chain.checked} blocks · height{" "}
          {chain.height}
          {chain.errors?.length ? (
            <ul className="mt-2 list-disc pl-5">
              {chain.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          ) : null}
        </div>
      )}

      <form onSubmit={onSearch} className="card mb-8 flex flex-col gap-2 sm:flex-row">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by block hash, tx id, or credential id"
        />
        <button type="submit" className="btn-primary shrink-0">
          Search
        </button>
      </form>

      {searchResult && (
        <div className="mb-10 space-y-4">
          <h2 className="font-serif text-xl font-semibold text-navy">Search results</h2>
          {!searchResult.blocks.length && !searchResult.transactions.length && (
            <p className="text-sm text-slate-500">No matches.</p>
          )}
          {searchResult.blocks.map((b) => (
            <div key={b.block_hash} className="card text-sm">
              Block #{b.index} · {truncateHash(b.block_hash)}
            </div>
          ))}
          {searchResult.transactions.map((t) => (
            <div key={t.transaction_id} className="card text-sm">
              <p className="font-medium text-navy">{t.transaction_type}</p>
              <p className="text-navy-400">
                {t.transaction_id}
                {t.credential_id ? ` · ${t.credential_id}` : ""}
                {t.block_index != null ? ` · block ${t.block_index}` : ""}
              </p>
            </div>
          ))}
        </div>
      )}

      <h2 className="font-serif text-xl font-semibold text-navy">Recent blocks</h2>
      {loading ? (
        <LoadingBlock />
      ) : (
        <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Index</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Hash</th>
                <th className="px-4 py-3">Txs</th>
                <th className="px-4 py-3">Validator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {blocks.map((b) => (
                <tr key={b.block_hash} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-medium tabular-nums text-navy">{b.index}</td>
                  <td className="px-4 py-3 text-navy-400">{formatDateTime(b.timestamp)}</td>
                  <td className="px-4 py-3 font-mono text-xs text-navy-500">
                    {truncateHash(b.block_hash, 8)}
                  </td>
                  <td className="px-4 py-3 tabular-nums">{b.transaction_count}</td>
                  <td className="px-4 py-3 text-navy-400">{b.validator}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
