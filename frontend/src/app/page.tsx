import Link from "next/link";
import { NetworkStats } from "@/components/NetworkStats";
import { apiDocsUrl } from "@/lib/api";

const STEPS = [
  { code: "ISSUE", title: "Issue", body: "An authorized institution creates a credential for a holder." },
  { code: "SIGN", title: "Sign", body: "The issuer signs with its Ed25519 identity key." },
  { code: "ANCHOR", title: "Anchor", body: "A hash and proof are written to the PTN ledger." },
  { code: "OWN", title: "Own", body: "The holder stores credentials in their wallet and PTN CV." },
  { code: "VERIFY", title: "Verify", body: "Anyone can check signature, integrity, and ledger proof." },
];

const USE_CASES = [
  {
    title: "Universities & boards",
    body: "Issue degrees, diplomas, and transcripts that employers can verify in seconds.",
  },
  {
    title: "Employers",
    body: "Confirm professional certifications without collecting fragile PDF copies.",
  },
  {
    title: "Training providers",
    body: "Issue course completion and skill evidence with lasting auditability.",
  },
  {
    title: "Individuals",
    body: "Own a portable wallet of credentials and publish a verifiable CV.",
  },
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-navy text-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <div className="container-ptn relative py-20 sm:py-28">
          <p className="font-serif text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
            Pakistan Trust Network
          </p>
          <h1 className="mt-4 max-w-2xl font-serif text-xl font-medium text-slate-200 sm:text-2xl">
            Open-source infrastructure for verifiable credentials.
          </h1>
          <p className="mt-6 font-serif text-lg tracking-wide text-accent-light">
            Issue. Own. Verify.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link href="/explorer" className="btn bg-white text-navy hover:bg-slate-100">
              Explore PTN
            </Link>
            <Link href="/register" className="btn bg-accent text-white hover:bg-accent-dark">
              Create Account
            </Link>
            <Link href="/verify/demo" className="btn border border-white/30 text-white hover:bg-white/10">
              Verify a Credential
            </Link>
            <Link href="/run" className="btn border border-white/30 text-white hover:bg-white/10">
              Download & run locally
            </Link>
            <a
              href="https://github.com/AmmarJamshed/pakistan-trust-network"
              target="_blank"
              rel="noreferrer"
              className="btn border border-white/30 text-white hover:bg-white/10"
            >
              View GitHub
            </a>
            <a
              href={apiDocsUrl()}
              target="_blank"
              rel="noreferrer"
              className="btn border border-white/30 text-white hover:bg-white/10"
            >
              API Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Why PTN */}
      <section className="container-ptn py-16 sm:py-20">
        <h2 className="section-title">Why PTN?</h2>
        <p className="mt-4 max-w-3xl text-navy-400 leading-relaxed">
          Credentials today live as PDFs, paper, and siloed databases—easy to forge, hard to
          verify, and controlled by issuers rather than holders. Pakistan Trust Network provides a
          shared, open protocol: institutions issue cryptographically signed credentials; holders
          own them; third parties verify issuance without calling the issuer each time.
        </p>
        <div className="mt-10 grid gap-6 sm:grid-cols-3">
          {[
            {
              t: "Tamper-evident",
              d: "Any change to credential content breaks the integrity hash.",
            },
            {
              t: "Issuer-bound",
              d: "Signatures map to registered organization identities on the network.",
            },
            {
              t: "Holder-centric",
              d: "Wallet and CV put control with the individual, not a central silo.",
            },
          ].map((item) => (
            <div key={item.t} className="border-t-2 border-accent pt-4">
              <h3 className="font-serif text-lg font-semibold text-navy">{item.t}</h3>
              <p className="mt-2 text-sm text-navy-400">{item.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-slate-200 bg-white py-16 sm:py-20">
        <div className="container-ptn">
          <h2 className="section-title">How it works</h2>
          <p className="mt-3 text-sm text-navy-400">
            ISSUE → SIGN → ANCHOR → OWN → VERIFY
          </p>
          <ol className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((s, i) => (
              <li key={s.code} className="relative">
                <span className="font-serif text-3xl text-slate-200">{String(i + 1).padStart(2, "0")}</span>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wider text-accent">
                  {s.code}
                </p>
                <h3 className="mt-1 font-serif text-lg font-semibold text-navy">{s.title}</h3>
                <p className="mt-2 text-sm text-navy-400">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Use cases */}
      <section className="container-ptn py-16 sm:py-20">
        <h2 className="section-title">Use cases</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {USE_CASES.map((u) => (
            <div key={u.title} className="card">
              <h3 className="font-serif text-lg font-semibold text-navy">{u.title}</h3>
              <p className="mt-2 text-sm text-navy-400">{u.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* For Institutions */}
      <section className="border-y border-slate-200 bg-white py-16 sm:py-20">
        <div className="container-ptn grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <h2 className="section-title">For Institutions</h2>
            <p className="mt-4 text-navy-400 leading-relaxed">
              Register your organization, obtain a signing identity, and issue credentials through
              the PTN API or web console. Revocations are recorded on the ledger so verifiers see
              current status.
            </p>
            <Link href="/org" className="btn-primary mt-6">
              Organization portal
            </Link>
          </div>
          <ul className="space-y-3 text-sm text-navy-500">
            <li className="flex gap-2">
              <span className="text-accent">✓</span> Role-based issuance (owner, issuer, admin)
            </li>
            <li className="flex gap-2">
              <span className="text-accent">✓</span> Ed25519 issuer identities
            </li>
            <li className="flex gap-2">
              <span className="text-accent">✓</span> Append-only ledger anchoring
            </li>
            <li className="flex gap-2">
              <span className="text-accent">✓</span> Public verification URLs and QR targets
            </li>
          </ul>
        </div>
      </section>

      {/* For Developers */}
      <section className="container-ptn py-16 sm:py-20">
        <h2 className="section-title">For Developers</h2>
        <p className="mt-4 max-w-2xl text-navy-400">
          Integrate via REST. OpenAPI docs ship with the API. Example: verify a credential.
        </p>
        <pre className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-navy p-5 text-sm leading-relaxed text-slate-200">
          <code>{`# Verify a credential (public, no auth)
curl "$API/api/verify/CREDENTIAL_ID"

# Issue (authenticated org member)
curl -X POST "$API/api/credentials" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "organization_id": "...",
    "holder_email": "student@example.com",
    "type_code": "UniversityDegree",
    "title": "BSc Computer Science"
  }'`}</code>
        </pre>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/docs" className="btn-outline">
            Frontend docs
          </Link>
          <a href={apiDocsUrl()} target="_blank" rel="noreferrer" className="btn-accent">
            Open API docs
          </a>
        </div>
      </section>

      {/* For Individuals */}
      <section className="border-y border-slate-200 bg-white py-16 sm:py-20">
        <div className="container-ptn">
          <h2 className="section-title">For Individuals</h2>
          <p className="mt-4 max-w-2xl text-navy-400 leading-relaxed">
            Create an account, receive credentials from issuing organizations, manage them in your
            wallet, and publish a PTN CV with verified badges that link to live verification pages.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register" className="btn-primary">
              Create account
            </Link>
            <Link href="/wallet" className="btn-outline">
              Open wallet
            </Link>
            <Link href="/cv" className="btn-outline">
              Manage CV
            </Link>
          </div>
        </div>
      </section>

      {/* Run locally */}
      <section className="border-y border-slate-200 bg-white py-16 sm:py-20">
        <div className="container-ptn">
          <h2 className="section-title">Run it yourself</h2>
          <p className="mt-4 max-w-3xl text-navy-400 leading-relaxed">
            There is no required cloud VPS. Each person downloads PTN, runs it on{" "}
            <strong className="font-medium text-navy">localhost</strong>, and Git Bash in the
            backend keeps public ledger proofs in sync through one GitHub repo.
          </p>
          <pre className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-navy p-5 text-sm text-slate-200">
            <code>{`git clone https://github.com/AmmarJamshed/pakistan-trust-network.git
cd pakistan-trust-network
join-network.bat`}</code>
          </pre>
          <Link href="/run" className="btn-primary mt-6">
            Download instructions
          </Link>
        </div>
      </section>

      {/* Live stats */}
      <section className="container-ptn py-16 sm:py-20">
        <h2 className="section-title">Live network</h2>
        <p className="mt-3 text-sm text-navy-400">Public counters from the PTN API.</p>
        <div className="mt-8">
          <NetworkStats />
        </div>
      </section>

      {/* Disclaimer */}
      <section className="border-t border-slate-200 bg-slate-100/80 py-10">
        <div className="container-ptn">
          <p className="text-sm leading-relaxed text-slate-600">
            <strong className="font-medium text-navy">Disclaimer:</strong> Pakistan Trust Network is
            an open-source prototype and reference implementation for verifiable credentials. It is
            not a government service and is not endorsed by any government organization. Demo
            credentials and organizations are labelled as such and must not be treated as official
            records.
          </p>
        </div>
      </section>
    </div>
  );
}
