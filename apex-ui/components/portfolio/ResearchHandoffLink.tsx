"use client";

import Link from "next/link";

export default function ResearchHandoffLink({ symbol }: { symbol: string | null }) {
  if (!symbol) {
    return null;
  }

  const href = `/app/research?symbol=${encodeURIComponent(symbol)}`;

  return (
    <section className="rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-3">
      <p className="text-sm text-blue-50/90">
        Research {symbol} before changing allocation.
      </p>
      <Link
        href={href}
        className="mt-2 inline-flex text-sm font-medium text-blue-100 underline-offset-4 hover:underline"
      >
        Open research workspace
      </Link>
    </section>
  );
}
