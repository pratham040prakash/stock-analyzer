"use client";

import { formatInr, fundsGuidanceText } from "@/lib/funds";
import type { Intent } from "@/types/intent";
import { ApexBody, ApexCard, ApexTitle } from "@/components/ui/apex";

type Props = {
  availableCash: number;
  intent: Intent;
  loading?: boolean;
};

export function AvailableFundsCardSkeleton() {
  return (
    <ApexCard hover={false} padding="compact">
      <div className="h-3 w-28 rounded bg-white/10 animate-pulse" />
      <div className="mt-3 h-8 w-32 rounded bg-white/10 animate-pulse" />
    </ApexCard>
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
    <ApexCard hover={false} padding="compact">
      <ApexBody>Cash available</ApexBody>
      <ApexTitle className="mt-2 text-[22px]">
        {formatInr(availableCash)}
      </ApexTitle>
      <ApexBody
        className={`mt-2 ${isEmpty ? "text-amber-200/80" : "text-emerald-200/70"}`}
      >
        {guidance}
      </ApexBody>
    </ApexCard>
  );
}
