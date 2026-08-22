import Link from "next/link";

type Props = {
  label?: string;
  href?: string;
  verified?: boolean;
};

export function VerifiedBadge({ label = "VERIFIED", href, verified = true }: Props) {
  const className = verified ? "badge-verified" : "badge-revoked";
  const text = verified ? label : "REVOKED / UNVERIFIED";

  if (href && verified) {
    return (
      <Link href={href} className={`${className} hover:underline`}>
        <span aria-hidden>✓</span> {text}
      </Link>
    );
  }

  return (
    <span className={className}>
      <span aria-hidden>{verified ? "✓" : "✗"}</span> {text}
    </span>
  );
}
