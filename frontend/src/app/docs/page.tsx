import Link from "next/link";
import { apiDocsUrl, API_BASE } from "@/lib/api";
import { PageHeader } from "@/components/ui";

export const metadata = {
  title: "Documentation",
};

export default function DocsPage() {
  const docs = apiDocsUrl();

  return (
    <div className="container-ptn max-w-3xl py-12">
      <PageHeader
        title="Documentation"
        subtitle="Integrate with the Pakistan Trust Network API."
      />

      <div className="space-y-6">
        <div className="card">
          <h2 className="font-serif text-lg font-semibold text-navy">API reference</h2>
          <p className="mt-2 text-sm text-navy-400">
            Interactive OpenAPI docs are served by the backend.
          </p>
          <a
            href={docs}
            target="_blank"
            rel="noreferrer"
            className="btn-accent mt-4 inline-flex"
          >
            Open {docs}
          </a>
          <p className="mt-3 text-xs text-slate-500">
            API base: {API_BASE || "same origin (proxied /api)"}
          </p>
        </div>

        <div className="card space-y-3 text-sm text-navy-400">
          <h2 className="font-serif text-lg font-semibold text-navy">Key endpoints</h2>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <code className="text-navy">POST /api/auth/register</code>,{" "}
              <code className="text-navy">POST /api/auth/login</code>,{" "}
              <code className="text-navy">GET /api/auth/me</code>
            </li>
            <li>
              <code className="text-navy">POST /api/organizations</code>,{" "}
              <code className="text-navy">GET /api/organizations/mine</code>
            </li>
            <li>
              <code className="text-navy">POST /api/credentials</code>,{" "}
              <code className="text-navy">GET /api/verify/:id</code>
            </li>
            <li>
              <code className="text-navy">GET /api/wallet/me</code>,{" "}
              <code className="text-navy">GET/POST /api/cv/…</code>
            </li>
            <li>
              <code className="text-navy">GET /api/ledger/blocks</code>,{" "}
              <code className="text-navy">GET /api/ledger/verify-chain</code>
            </li>
            <li>
              <code className="text-navy">GET /api/stats</code>,{" "}
              <code className="text-navy">GET /api/admin/overview</code>
            </li>
          </ul>
        </div>

        <div className="flex flex-wrap gap-3">
          <a
            href="https://github.com/ptn-network/ptn"
            target="_blank"
            rel="noreferrer"
            className="btn-outline"
          >
            GitHub repository
          </a>
          <Link href="/fraud-demo" className="btn-outline">
            Integrity fraud demo
          </Link>
        </div>

        <p className="text-xs text-slate-500">
          PTN is an open-source prototype. Not affiliated with or endorsed by any government
          organization.
        </p>
      </div>
    </div>
  );
}
