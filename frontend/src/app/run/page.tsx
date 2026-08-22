"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui";

const HUB = "https://github.com/AmmarJamshed/pakistan-trust-network";
const ZIP = `${HUB}/archive/refs/heads/main.zip`;

type Status = {
  enabled: boolean;
  repo_root: string | null;
  git_bash: string | null;
  remote: string;
  last_sync: string | null;
  last_error: string | null;
  last_result: Record<string, unknown> | null;
  running: boolean;
};

export default function RunLocalPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    try {
      setStatus(await api.network.status());
    } catch {
      setStatus(null);
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, []);

  async function syncNow() {
    setSyncing(true);
    setMessage(null);
    try {
      const result = await api.network.sync();
      setMessage(JSON.stringify(result, null, 2));
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="container-ptn max-w-3xl py-12">
      <PageHeader
        title="Run PTN on your machine"
        subtitle="Download the app, use localhost, and connect to the shared GitHub hub. No VPS required."
      />

      <div className="space-y-6">
        <div className="card">
          <h2 className="font-serif text-lg font-semibold text-navy">1. Download</h2>
          <p className="mt-2 text-sm text-navy-400">
            Prefer git clone so your node can pull and push public ledger proofs. A ZIP gives you
            the code only.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <a href={HUB} className="btn-primary" target="_blank" rel="noreferrer">
              Open GitHub
            </a>
            <a href={ZIP} className="btn-outline">
              Download ZIP
            </a>
          </div>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-navy p-4 text-xs text-slate-200">
            {`git clone ${HUB}.git
cd pakistan-trust-network
join-network.bat`}
          </pre>
        </div>

        <div className="card">
          <h2 className="font-serif text-lg font-semibold text-navy">2. Use localhost</h2>
          <p className="mt-2 text-sm text-navy-400">
            After start, open the website on this computer. Other people run the same commands on
            their computers — each node is localhost, the shared access point is GitHub.
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-navy-400">
            <li>
              Website: <code>http://localhost:3001</code>
            </li>
            <li>
              API: <code>http://localhost:8080/api/docs</code>
            </li>
          </ul>
        </div>

        <div className="card">
          <h2 className="font-serif text-lg font-semibold text-navy">3. Git Bash mesh</h2>
          <p className="mt-2 text-sm text-navy-400">
            The backend uses Git Bash (when installed) to pull <code>network/ledger/snapshot.json</code>{" "}
            from the hub repo, merge public proofs into this node, and push new proofs if you have
            permission. Private keys, passwords, and private credential data stay off Git.
          </p>
          <p className="mt-3 text-sm text-navy-400">
            To publish proofs from your node, add a GitHub personal access token as{" "}
            <code>PTN_NETWORK_GIT_TOKEN</code> in <code>backend/.env</code> (repo Contents: write),
            or become a collaborator on the hub repository.
          </p>
        </div>

        <div className="card">
          <h2 className="font-serif text-lg font-semibold text-navy">This node</h2>
          {status ? (
            <dl className="mt-3 grid gap-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Git mesh</dt>
                <dd>{status.enabled ? "Enabled" : "Disabled — set PTN_NETWORK_ENABLED=true"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Git Bash</dt>
                <dd className="truncate">{status.git_bash || "Not found"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Repo</dt>
                <dd className="truncate">{status.repo_root || "Not a git clone"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Last sync</dt>
                <dd>{status.last_sync || "Never"}</dd>
              </div>
              {status.last_error ? (
                <p className="text-red-700">{status.last_error}</p>
              ) : null}
            </dl>
          ) : (
            <p className="mt-3 text-sm text-navy-400">API not reachable. Start the backend first.</p>
          )}
          <button type="button" className="btn-accent mt-4" onClick={syncNow} disabled={syncing}>
            {syncing ? "Syncing…" : "Sync with GitHub now"}
          </button>
          {message ? (
            <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs">{message}</pre>
          ) : null}
        </div>
      </div>
    </div>
  );
}
