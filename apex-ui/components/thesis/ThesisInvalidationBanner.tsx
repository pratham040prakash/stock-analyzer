"use client";

import Link from "next/link";
import type { ThesisInvalidationWarning } from "@/types/thesisInvalidation";

type Props = {
  warnings: ThesisInvalidationWarning[];
};

export default function ThesisInvalidationBanner({ warnings }: Props) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-4 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-amber-100/70">
        Thesis watch
      </p>
      <ul className="space-y-2 text-sm text-amber-100/90">
        {warnings.map((warning) => (
          <li key={warning.symbol}>
            {warning.message}{" "}
            <Link
              href={`/app/research?symbol=${encodeURIComponent(warning.symbol)}`}
              className="text-blue-200/90 hover:text-blue-100"
            >
              Review thesis →
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
