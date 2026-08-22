"use client";

type Props = {
  children: React.ReactNode;
  className?: string;
};

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-navy">{title}</h1>
        {subtitle && <p className="mt-2 max-w-2xl text-sm text-navy-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function EmptyState({ children, className = "" }: Props) {
  return (
    <div className={`rounded-lg border border-dashed border-slate-300 bg-white px-6 py-10 text-center text-sm text-slate-500 ${className}`}>
      {children}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
      {message}
    </div>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return <p className="py-8 text-center text-sm text-slate-500">{label}</p>;
}
