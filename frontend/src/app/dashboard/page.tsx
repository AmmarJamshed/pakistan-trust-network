"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import type { User } from "@/lib/api";
import { LoadingBlock, PageHeader } from "@/components/ui";

const tiles = [
  { href: "/wallet", title: "Credential wallet", desc: "View education, professional, skills, and achievement credentials." },
  { href: "/cv", title: "PTN CV", desc: "Publish a verifiable CV with links to live proofs." },
  { href: "/issue", title: "Issue credentials", desc: "Issue as an organization member." },
  { href: "/org", title: "Organizations", desc: "Create or manage your organizations." },
  { href: "/explorer", title: "Ledger explorer", desc: "Browse blocks and verify chain integrity." },
  { href: "/fraud-demo", title: "Fraud demo", desc: "See integrity failure on a modified credential." },
  { href: "/admin", title: "Admin", desc: "Network overview (admin role required)." },
  { href: "/docs", title: "Documentation", desc: "API docs and integration pointers." },
];

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentUser().then((u) => {
      if (!u) {
        requireAuthRedirect();
        return;
      }
      setUser(u);
      setLoading(false);
    });
  }, []);

  if (loading || !user) return <LoadingBlock />;

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title={`Welcome, ${user.full_name}`}
        subtitle={`${user.email} · ${user.role} · ${user.did}`}
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.href} href={t.href} className="card transition-colors hover:border-accent/40">
            <h2 className="font-serif text-lg font-semibold text-navy">{t.title}</h2>
            <p className="mt-2 text-sm text-navy-400">{t.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
