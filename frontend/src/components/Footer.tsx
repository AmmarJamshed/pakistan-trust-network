import Link from "next/link";
import { apiDocsUrl } from "@/lib/api";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      <div className="container-ptn py-10">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2">
            <p className="font-serif text-lg font-semibold text-navy">Pakistan Trust Network</p>
            <p className="mt-2 max-w-md text-sm leading-relaxed text-navy-400">
              Open-source infrastructure for issuing, owning, and verifying educational and
              professional credentials. Proof on-chain, data off-chain.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Product</p>
            <ul className="mt-3 space-y-2 text-sm text-navy-400">
              <li>
                <Link href="/explorer" className="hover:text-navy">
                  Explorer
                </Link>
              </li>
              <li>
                <Link href="/wallet" className="hover:text-navy">
                  Wallet
                </Link>
              </li>
              <li>
                <Link href="/cv" className="hover:text-navy">
                  PTN CV
                </Link>
              </li>
              <li>
                <Link href="/fraud-demo" className="hover:text-navy">
                  Fraud demo
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Developers</p>
            <ul className="mt-3 space-y-2 text-sm text-navy-400">
              <li>
                <Link href="/docs" className="hover:text-navy">
                  Documentation
                </Link>
              </li>
              <li>
                <a href={apiDocsUrl()} className="hover:text-navy" target="_blank" rel="noreferrer">
                  API reference
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/AmmarJamshed/pakistan-trust-network"
                  className="hover:text-navy"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-slate-100 pt-6">
          <p className="text-xs leading-relaxed text-slate-500">
            Pakistan Trust Network is an open-source prototype and reference implementation. It is{" "}
            <strong className="font-medium text-slate-600">
              not affiliated with, endorsed by, or operated by any government organization
            </strong>
            . Credential verification confirms cryptographic issuance and ledger anchoring—not
            government authenticity.
          </p>
        </div>
      </div>
    </footer>
  );
}
