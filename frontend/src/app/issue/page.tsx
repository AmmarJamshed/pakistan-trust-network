"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, type Credential, type Organization } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

const TYPE_CODES = [
  "UniversityDegree",
  "Diploma",
  "Certificate",
  "CourseCompletion",
  "Employment",
  "Internship",
  "ProfessionalCertification",
  "Training",
  "SkillEvidence",
  "Award",
  "Project",
];

export default function IssuePage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [issued, setIssued] = useState<Credential[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [holderEmail, setHolderEmail] = useState("");
  const [typeCode, setTypeCode] = useState(TYPE_CODES[0]);
  const [title, setTitle] = useState("");
  const [subjectJson, setSubjectJson] = useState('{\n  "degree": "",\n  "program": ""\n}');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      const user = await getCurrentUser();
      if (!user) {
        requireAuthRedirect();
        return;
      }
      try {
        const mine = await api.organizations.mine();
        setOrgs(mine);
        if (mine[0]) {
          setOrganizationId(mine[0].id);
          const list = await api.credentials.list(mine[0].id);
          setIssued(list);
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load organizations");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function onOrgChange(id: string) {
    setOrganizationId(id);
    if (!id) return;
    try {
      setIssued(await api.credentials.list(id));
    } catch {
      setIssued([]);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    let subject: Record<string, unknown> = {};
    try {
      subject = JSON.parse(subjectJson || "{}");
    } catch {
      setError("Credential subject must be valid JSON");
      setBusy(false);
      return;
    }
    try {
      const cred = await api.credentials.issue({
        organization_id: organizationId,
        holder_email: holderEmail,
        type_code: typeCode,
        title,
        credential_subject: subject,
        public_fields: Object.keys(subject),
      });
      setSuccess(`Issued ${cred.credential_id}`);
      setTitle("");
      setIssued(await api.credentials.list(organizationId));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Issuance failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="Issue credential"
        subtitle="Available to organization members with issuer privileges."
        actions={
          <Link href="/org" className="btn-outline">
            Manage organizations
          </Link>
        }
      />
      {error && <ErrorBanner message={error} />}
      {success && (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-accent">
          {success}
        </div>
      )}

      {!orgs.length ? (
        <div className="card text-sm text-navy-400">
          You are not a member of any organization.{" "}
          <Link href="/org" className="text-accent hover:underline">
            Create one
          </Link>{" "}
          to start issuing.
        </div>
      ) : (
        <form onSubmit={onSubmit} className="card mb-10 max-w-xl space-y-4">
          <div>
            <label className="label" htmlFor="org">
              Organization
            </label>
            <select
              id="org"
              className="input"
              value={organizationId}
              onChange={(e) => onOrgChange(e.target.value)}
              required
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name} ({o.status})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="holder">
              Holder email
            </label>
            <input
              id="holder"
              type="email"
              className="input"
              required
              value={holderEmail}
              onChange={(e) => setHolderEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="type">
              Type
            </label>
            <select
              id="type"
              className="input"
              value={typeCode}
              onChange={(e) => setTypeCode(e.target.value)}
            >
              {TYPE_CODES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="title">
              Title
            </label>
            <input
              id="title"
              className="input"
              required
              minLength={2}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="subject">
              Credential subject (JSON)
            </label>
            <textarea
              id="subject"
              className="input min-h-[120px] font-mono text-xs"
              value={subjectJson}
              onChange={(e) => setSubjectJson(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Issuing…" : "Issue credential"}
          </button>
        </form>
      )}

      {issued.length > 0 && (
        <section>
          <h2 className="font-serif text-xl font-semibold text-navy">Recently issued</h2>
          <ul className="mt-4 space-y-2">
            {issued.slice(0, 20).map((c) => (
              <li key={c.credential_id} className="card flex flex-wrap items-center justify-between gap-2 text-sm">
                <div>
                  <p className="font-medium text-navy">{c.title}</p>
                  <p className="text-navy-400">
                    {c.credential_id} · {c.status} · {formatDate(c.issued_at)}
                  </p>
                </div>
                <Link href={`/verify/${c.credential_id}`} className="btn-ghost">
                  Verify
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
