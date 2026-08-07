"use client";

import { formatInr, fundsGuidanceText } from "@/lib/funds";
import type { Intent } from "@/types/intent";

type Props = {
  availableCash: number;
  intent: Intent;
  loading?: boolean;
};

export function AvailableFundsCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-800/40 p-5 space-y-3">
      <div className="h-3 w-28 rounded bg-white/10 animate-pulse" />
      <div className="h-9 w-32 rounded bg-white/10 animate-pulse" />
      <div className="h-4 w-40 rounded bg-white/10 animate-pulse" />
    </div>
  );
}

export default function AvailableFundsCard({
  availableCash,
  intent,
  loading = false,
}: Props) {
  if (loading) {
    return <AvailableFundsCardSkeleton />;
  }

  const guidance = fundsGuidanceText(availableCash, intent);
  const isEmpty = availableCash <= 0;

  return (
    <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-slate-900/80 to-slate-900/40 p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
        Available to Invest
      </p>
      <p
        className={`text-3xl font-semibold tracking-tight ${
          isEmpty ? "text-gray-400" : "text-emerald-50"
        }`}
      >
        {formatInr(availableCash)}
      </p>
      <p
        className={`mt-2 text-sm ${
          isEmpty ? "text-amber-200/90" : "text-emerald-200/80"
        }`}
      >
        {guidance}
      </p>
    </div>
  );
}
