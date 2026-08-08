"use client";

import type { DailyInsight } from "@/types/dailyInsight";
import { ApexBody, ApexCard, ApexEyebrow } from "@/components/ui/apex";

type Props = {
  insight: DailyInsight;
};

function pnlClass(dayPnl: number | null): string {
  if (dayPnl === null) {
    return "text-apex-text";
  }
  if (dayPnl > 0) {
    return "text-emerald-300";
  }
  if (dayPnl < 0) {
    return "text-red-300";
  }
  return "text-apex-muted";
}

export default function DailyInsightBanner({ insight }: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      <ApexEyebrow className="mb-2">Market note</ApexEyebrow>
      <p className={`text-[15px] font-medium ${pnlClass(insight.day_pnl)}`}>
        {insight.pnl_line}
      </p>
      <ApexBody className="mt-2">{insight.guidance}</ApexBody>
    </ApexCard>
  );
}
