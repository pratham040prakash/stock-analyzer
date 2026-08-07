import { formatInr } from "@/lib/funds";
import type {
  DecisionOpportunity,
  RecommendedAllocationItem,
} from "@/types/decision";

type Props = {
  opportunities: DecisionOpportunity[];
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
  plan,
  onBack,
}: Props) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Opportunities to explore
        </p>
        <button
          type="button"
          onClick={onBack}
          className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
        >
          ← Back
        </button>
      </div>

      <ul className="space-y-2">
        {opportunities.map((opportunity) => {
          const amount = amountForName(plan, opportunity.name);

          return (
            <li
              key={opportunity.name}
              className="rounded-xl border border-purple-500/20 bg-purple-500/5 px-4 py-3"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-purple-50">
                    {opportunity.name}
                  </p>
                  <p className="text-xs text-purple-200/70 mt-1">
                    {opportunity.type}
                  </p>
                </div>
                {amount !== null && amount > 0 && (
                  <span className="shrink-0 text-sm font-medium text-purple-100">
                    {formatInr(amount)}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {plan.length > 0 && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 space-y-1.5">
          <p className="text-xs text-gray-500 uppercase tracking-wider">
            Suggested allocation
          </p>
          {plan.map((item) => (
            <p key={item.name} className="text-sm text-purple-50">
              {formatInr(item.amount)} → {item.name}
            </p>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-500">
        Research in your broker first — guidance only, not a buy recommendation.
      </p>
    </div>
  );
}
