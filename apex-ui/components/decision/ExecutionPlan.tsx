"use client";

import { useState } from "react";
import { formatInr } from "@/lib/funds";
import type { RecommendedAllocationItem } from "@/types/decision";
import { ApexBody, ApexButton, ApexEyebrow, ApexRow, ApexSection } from "@/components/ui/apex";

type Props = {
  items: RecommendedAllocationItem[];
  allItems?: RecommendedAllocationItem[];
  onBack: () => void;
};

export default function ExecutionPlan({
  items,
  allItems,
  onBack,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const expandedList = allItems ?? items;
  const visibleItems = expanded ? expandedList : items;
  const hasAmounts = items.some((item) => item.amount > 0);
  const canExpand = expandedList.length > items.length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <ApexEyebrow>Allocation plan</ApexEyebrow>
        <button
          type="button"
          onClick={onBack}
          className="text-[13px] text-apex-muted transition-colors hover:text-apex-text"
        >
          Back
        </button>
      </div>

      {hasAmounts ? (
        <ApexBody className="text-emerald-200/80">
          Deploy {formatInr(items.reduce((sum, item) => sum + item.amount, 0))}{" "}
          when you are ready in your broker.
        </ApexBody>
      ) : visibleItems.length > 0 ? (
        <ApexBody className="text-amber-200/80">
          Target instruments for your next buy.
        </ApexBody>
      ) : (
        <ApexBody>Building your plan…</ApexBody>
      )}

      {visibleItems.length > 0 ? (
        <>
          <ApexSection className="rounded-xl border border-apex-border px-4">
            {visibleItems.map((item) => (
              <ApexRow
                key={item.name}
                label={item.name}
                value={
                  item.amount > 0 ? formatInr(item.amount) : item.reason
                }
              />
            ))}
          </ApexSection>

          {canExpand ? (
            <button
              type="button"
              onClick={() => setExpanded((open) => !open)}
              className="text-[13px] text-blue-200/80 transition-colors hover:text-blue-100"
            >
              {expanded ? "Show less" : "Show all options"}
            </button>
          ) : null}
        </>
      ) : null}

      <ApexButton variant="secondary" onClick={onBack}>
        Done
      </ApexButton>
    </div>
  );
}
