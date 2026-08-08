"use client";

import { useState } from "react";
import { formatInr } from "@/lib/funds";
import type {
  DecisionOpportunity,
  RecommendedAllocationItem,
} from "@/types/decision";
import { ApexBody, ApexButton, ApexEyebrow, ApexRow, ApexSection } from "@/components/ui/apex";

type Props = {
  opportunities: DecisionOpportunity[];
  allOpportunities?: DecisionOpportunity[];
  plan: RecommendedAllocationItem[];
  onBack: () => void;
};

function amountForName(
  plan: RecommendedAllocationItem[],
  name: string,
): number | null {
  const match = plan.find((item) => item.name === name);
  return match?.amount ?? null;
}

export default function OpportunitiesList({
  opportunities,
  allOpportunities,
  plan,
  onBack,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const expandedList = allOpportunities ?? opportunities;
  const visibleOpportunities = expanded ? expandedList : opportunities;
  const canExpand = expandedList.length > opportunities.length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <ApexEyebrow>Ideas to explore</ApexEyebrow>
        <button
          type="button"
          onClick={onBack}
          className="text-[13px] text-apex-muted transition-colors hover:text-apex-text"
        >
          Back
        </button>
      </div>

      {visibleOpportunities.length > 0 ? (
        <ApexSection className="rounded-xl border border-apex-border px-4">
          {visibleOpportunities.map((opportunity) => {
            const amount = amountForName(plan, opportunity.name);

            return (
              <ApexRow
                key={opportunity.name}
                label={opportunity.name}
                value={
                  amount && amount > 0
                    ? formatInr(amount)
                    : opportunity.type
                }
              />
            );
          })}
        </ApexSection>
      ) : (
        <ApexBody>No opportunities surfaced today.</ApexBody>
      )}

      {canExpand ? (
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          className="text-[13px] text-blue-200/80 transition-colors hover:text-blue-100"
        >
          {expanded ? "Show less" : "Show all ideas"}
        </button>
      ) : null}

      <ApexButton variant="secondary" onClick={onBack}>
        Done
      </ApexButton>
    </div>
  );
}
