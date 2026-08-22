"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getCurrentUser, logout } from "@/lib/auth";
import type { User } from "@/lib/api";

const links = [
  { href: "/run", label: "Run locally" },
  { href: "/explorer", label: "Explorer" },
  { href: "/verify/demo", label: "Verify" },
  { href: "/docs", label: "Docs" },
];

export function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="container-ptn flex h-16 items-center justify-between">
        <Link href="/" className="font-serif text-xl font-semibold tracking-tight text-navy">
          PTN
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-navy-400 transition-colors hover:text-navy"
            >
              {l.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link href="/dashboard" className="text-sm text-navy-400 hover:text-navy">
                Dashboard
              </Link>
              <Link href="/wallet" className="text-sm text-navy-400 hover:text-navy">
                Wallet
              </Link>
              <button type="button" onClick={logout} className="btn-ghost text-sm">
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm text-navy-400 hover:text-navy">
                Sign in
              </Link>
              <Link href="/register" className="btn-primary text-sm">
                Create account
              </Link>
            </>
          )}
        </nav>

        <button
          type="button"
          className="btn-ghost md:hidden"
          aria-label="Toggle menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="text-lg leading-none">{open ? "✕" : "☰"}</span>
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-white md:hidden">
          <div className="container-ptn flex flex-col gap-3 py-4">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="text-sm text-navy"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            {user ? (
              <>
                <Link href="/dashboard" onClick={() => setOpen(false)}>
                  Dashboard
                </Link>
                <Link href="/wallet" onClick={() => setOpen(false)}>
                  Wallet
                </Link>
                <button type="button" onClick={logout} className="text-left text-sm text-navy-400">
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" onClick={() => setOpen(false)}>
                  Sign in
                </Link>
                <Link href="/register" className="btn-primary w-fit" onClick={() => setOpen(false)}>
                  Create account
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
