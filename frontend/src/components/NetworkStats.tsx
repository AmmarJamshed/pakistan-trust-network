"use client";

import { useEffect, useState } from "react";
import { api, type Stats } from "@/lib/api";

export function NetworkStats() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .stats()
      .then(setStats)
      .catch(() => setError("Network stats unavailable"));
  }, []);

  if (error) {
    return <p className="text-sm text-slate-500">{error}</p>;
  }

  if (!stats) {
    return <p className="text-sm text-slate-500">Loading network stats…</p>;
  }

  const items = [
    { label: "Organizations", value: stats.organizations },
    { label: "Credentials issued", value: stats.credentials_issued },
    { label: "Active credentials", value: stats.active_credentials },
    { label: "Verifications", value: stats.credentials_verified },
    { label: "Ledger blocks", value: stats.blocks },
    { label: "Transactions", value: stats.transactions },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((item) => (
        <div key={item.label} className="border-l-2 border-accent/40 pl-3">
          <p className="font-serif text-2xl font-semibold text-navy tabular-nums">
            {item.value.toLocaleString()}
          </p>
          <p className="mt-1 text-xs text-slate-500">{item.label}</p>
        </div>
      ))}
    </div>
  );
}
