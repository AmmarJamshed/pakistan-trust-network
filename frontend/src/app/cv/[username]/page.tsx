"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/ui";

type PublicCv = Awaited<ReturnType<typeof api.cv.public>>;

function PublicCvContent() {
  const params = useParams();
  const search = useSearchParams();
  const username = String(params.username ?? "");
  const token = search.get("token") ?? undefined;

  const [cv, setCv] = useState<PublicCv | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;
    api.cv
      .public(username, token)
      .then(setCv)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "CV not found or not public")
      )
      .finally(() => setLoading(false));
  }, [username, token]);

  if (loading) return <LoadingBlock />;

  return (
    <div className="container-ptn max-w-3xl py-12">
      {error && <ErrorBanner message={error} />}
      {!cv ? (
        <EmptyState>This CV is private or does not exist.</EmptyState>
      ) : (
        <>
          <PageHeader title={cv.full_name} subtitle={cv.headline || `@${cv.username}`} />
          {cv.summary && <p className="mb-8 text-navy-400 leading-relaxed">{cv.summary}</p>}
          <div className="space-y-8">
            {Object.entries(cv.sections).map(([section, items]) => (
              <section key={section}>
                <h2 className="border-b border-slate-200 pb-2 font-serif text-xl font-semibold capitalize text-navy">
                  {section}
                </h2>
                <ul className="mt-4 space-y-4">
                  {items.map((item, idx) => (
                    <li
                      key={`${item.title}-${idx}`}
                      className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between"
                    >
                      <div>
                        <p className="font-medium text-navy">{item.title}</p>
                        {item.subtitle && (
                          <p className="text-sm text-navy-400">{item.subtitle}</p>
                        )}
                      </div>
                      {item.credential_id && (
                        <VerifiedBadge
                          verified={item.verified}
                          href={`/verify/${item.credential_id}`}
                        />
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
          <p className="mt-10 text-xs text-slate-500">{cv.disclaimer}</p>
        </>
      )}
    </div>
  );
}

export default function PublicCvPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <PublicCvContent />
    </Suspense>
  );
}
