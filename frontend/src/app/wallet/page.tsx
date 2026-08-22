"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError, type Wallet } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

const CATEGORY_ORDER = ["education", "professional", "skills", "achievement"] as const;
const CATEGORY_LABELS: Record<string, string> = {
  education: "Education",
  professional: "Professional",
  skills: "Skills",
  achievement: "Achievement",
};

export default function WalletPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
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
        setWallet(await api.wallet.me());
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load wallet");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="Credential wallet"
        subtitle={
          wallet
            ? `${wallet.holder.full_name} · ${wallet.count} credential${wallet.count === 1 ? "" : "s"}`
            : "Your issued credentials, grouped by category."
        }
        actions={
          <Link href="/cv" className="btn-outline">
            Manage CV
          </Link>
        }
      />
      {error && <ErrorBanner message={error} />}
      {!wallet || wallet.count === 0 ? (
        <EmptyState>
          No credentials yet. When an organization issues one to your account, it will appear here.
        </EmptyState>
      ) : (
        <div className="space-y-10">
          {CATEGORY_ORDER.map((cat) => {
            const items = wallet.categories[cat] ?? [];
            if (!items.length) return null;
            return (
              <section key={cat}>
                <h2 className="font-serif text-xl font-semibold text-navy">
                  {CATEGORY_LABELS[cat] ?? cat}
                </h2>
                <ul className="mt-4 space-y-3">
                  {items.map((c) => (
                    <li key={c.credential_id} className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-medium text-navy">{c.title}</h3>
                          <VerifiedBadge
                            verified={c.verified}
                            href={`/verify/${c.credential_id}`}
                          />
                          {c.is_demo && <span className="badge-pending">DEMO</span>}
                        </div>
                        <p className="mt-1 text-sm text-navy-400">
                          {c.issuer} · {c.type} · Issued {formatDate(c.issued_at)}
                        </p>
                      </div>
                      <Link href={`/verify/${c.credential_id}`} className="btn-outline shrink-0 text-sm">
                        Verify
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
