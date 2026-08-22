"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { registerAndStore } from "@/lib/auth";
import { ErrorBanner, PageHeader } from "@/components/ui";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [accountType, setAccountType] = useState("individual");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerAndStore({
        email,
        password,
        full_name: fullName,
        username: username || undefined,
        account_type: accountType,
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-ptn max-w-md py-12">
      <PageHeader
        title="Create account"
        subtitle="Join PTN as an individual holder or organization operator."
      />
      {error && <ErrorBanner message={error} />}
      <form onSubmit={onSubmit} className="card space-y-4">
        <div>
          <label className="label" htmlFor="fullName">
            Full name
          </label>
          <input
            id="fullName"
            className="input"
            required
            minLength={2}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="input"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="username">
            Username <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <input
            id="username"
            className="input"
            minLength={3}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Used for public CV URL"
          />
        </div>
        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="input"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="accountType">
            Account type
          </label>
          <select
            id="accountType"
            className="input"
            value={accountType}
            onChange={(e) => setAccountType(e.target.value)}
          >
            <option value="individual">Individual</option>
            <option value="organization">Organization</option>
          </select>
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-navy-400">
        Already registered?{" "}
        <Link href="/login" className="text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
