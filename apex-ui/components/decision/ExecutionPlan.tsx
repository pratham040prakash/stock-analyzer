import { formatInr } from "@/lib/funds";
import type { RecommendedAllocationItem } from "@/types/decision";

type Props = {
  items: RecommendedAllocationItem[];
  onBack: () => void;
};

export default function ExecutionPlan({ items, onBack }: Props) {
  const total = items.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Your execution plan
        </p>
        <button
          type="button"
          onClick={onBack}
          className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
        >
          ← Back
        </button>
      </div>

      {total > 0 && (
        <p className="text-sm text-emerald-200/90">
          Deploy {formatInr(total)} across these instruments in your broker.
        </p>
      )}

      <ul className="space-y-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
        {items.map((item) => (
          <li
            key={item.name}
            className="flex items-start justify-between gap-4 py-1"
          >
            <div>
              <p className="text-sm font-medium text-emerald-50">
                {formatInr(item.amount)} → {item.name}
              </p>
              <p className="text-xs text-emerald-200/70 mt-0.5">{item.reason}</p>
            </div>
          </li>
        ))}
      </ul>

      <p className="text-xs text-gray-500">
        Place these orders in Zerodha when you are ready — guidance only.
      </p>
    </div>
  );
}
