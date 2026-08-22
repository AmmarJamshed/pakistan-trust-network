type Props = {
  checks: Record<string, boolean>;
  overall?: string;
};

const CHECK_LABELS: { key: string; label: string }[] = [
  { key: "issuer_verified", label: "Issuer verified" },
  { key: "signature_verified", label: "Signature verified" },
  { key: "credential_integrity_verified", label: "Credential integrity" },
  { key: "ledger_proof_verified", label: "Ledger proof" },
  { key: "credential_active", label: "Active (not revoked)" },
  { key: "chain_integrity_verified", label: "Chain integrity" },
];

export function VerificationChecks({ checks, overall }: Props) {
  const overallTone =
    overall === "VERIFIED"
      ? "border-emerald-200 bg-emerald-50 text-accent"
      : overall === "REVOKED"
        ? "border-red-200 bg-red-50 text-red-800"
        : overall === "NOT_FOUND"
          ? "border-slate-200 bg-slate-50 text-slate-600"
          : "border-amber-200 bg-amber-50 text-amber-900";

  return (
    <div className="space-y-4">
      {overall && (
        <div className={`rounded-lg border px-4 py-3 text-center font-semibold ${overallTone}`}>
          Overall: {overall}
        </div>
      )}
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
        {CHECK_LABELS.map(({ key, label }) => {
          if (!(key in checks)) return null;
          const ok = Boolean(checks[key]);
          return (
            <li key={key} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
              <span className="text-navy-500">{label}</span>
              <span
                className={`font-medium ${ok ? "text-accent" : "text-red-600"}`}
                aria-label={ok ? "passed" : "failed"}
              >
                {ok ? "✓ Pass" : "✗ Fail"}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
