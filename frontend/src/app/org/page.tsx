"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, type Organization } from "@/lib/api";
import { getCurrentUser, requireAuthRedirect } from "@/lib/auth";
import { ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

const ORG_TYPES = [
  "UNIVERSITY",
  "SCHOOL",
  "COLLEGE",
  "EXAMINATION_BOARD",
  "TRAINING_PROVIDER",
  "EMPLOYER",
  "PROFESSIONAL_BODY",
  "GOVERNMENT",
  "OTHER",
];

export default function OrgPage() {
  const [mine, setMine] = useState<Organization[]>([]);
  const [publicOrgs, setPublicOrgs] = useState<Organization[]>([]);
  const [name, setName] = useState("");
  const [orgType, setOrgType] = useState("UNIVERSITY");
  const [email, setEmail] = useState("");
  const [website, setWebsite] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [m, list] = await Promise.all([
      api.organizations.mine(),
      api.organizations.list({ limit: 30 }),
    ]);
    setMine(m);
    setPublicOrgs(list);
  }

  useEffect(() => {
    (async () => {
      const user = await getCurrentUser();
      if (!user) {
        requireAuthRedirect();
        return;
      }
      setEmail(user.email);
      try {
        await refresh();
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Failed to load organizations");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.organizations.create({
        name,
        org_type: orgType,
        email,
        website: website || undefined,
        description: description || undefined,
        country: "Pakistan",
      });
      setName("");
      setDescription("");
      setWebsite("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn py-12">
      <PageHeader
        title="Organizations"
        subtitle="Register an issuing organization and manage membership."
        actions={
          <Link href="/issue" className="btn-primary">
            Issue credentials
          </Link>
        }
      />
      {error && <ErrorBanner message={error} />}

      <form onSubmit={onCreate} className="card mb-10 max-w-xl space-y-4">
        <h2 className="font-serif text-lg font-semibold text-navy">Create organization</h2>
        <div>
          <label className="label" htmlFor="name">
            Name
          </label>
          <input
            id="name"
            className="input"
            required
            minLength={2}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="type">
            Type
          </label>
          <select
            id="type"
            className="input"
            value={orgType}
            onChange={(e) => setOrgType(e.target.value)}
          >
            {ORG_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="email">
            Contact email
          </label>
          <input
            id="email"
            type="email"
            className="input"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="website">
            Website
          </label>
          <input
            id="website"
            className="input"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="https://"
          />
        </div>
        <div>
          <label className="label" htmlFor="desc">
            Description
          </label>
          <textarea
            id="desc"
            className="input min-h-[80px]"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy ? "Creating…" : "Create"}
        </button>
      </form>

      <section className="mb-10">
        <h2 className="font-serif text-xl font-semibold text-navy">Your organizations</h2>
        {!mine.length ? (
          <p className="mt-3 text-sm text-slate-500">None yet.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {mine.map((o) => (
              <li key={o.id} className="card text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-navy">{o.name}</p>
                  <span className="badge-neutral">{o.status}</span>
                </div>
                <p className="mt-1 text-navy-400">
                  {o.org_type} · {o.did}
                  {o.has_identity ? " · identity ready" : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="font-serif text-xl font-semibold text-navy">Network organizations</h2>
        <ul className="mt-4 space-y-2">
          {publicOrgs.map((o) => (
            <li key={o.id} className="flex items-center justify-between border-b border-slate-100 py-3 text-sm">
              <span className="text-navy">
                {o.name}
                {o.is_demo && <span className="ml-2 badge-pending">DEMO</span>}
              </span>
              <span className="text-navy-400">{o.status}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
