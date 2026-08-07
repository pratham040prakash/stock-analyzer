"use client";

import type { DailyDecisionOutput, DailyDecisionType } from "@/types/decision";

type Props = {
  decision: DailyDecisionOutput;
};

function decisionLabel(decision: DailyDecisionType): string {
  switch (decision) {
    case "BUY_MORE":
      return "Buy more";
    case "REDUCE":
      return "Reduce";
    case "WAIT":
      return "Wait";
    default:
      return "Hold";
  }
}

function decisionTone(decision: DailyDecisionType): string {
  switch (decision) {
    case "BUY_MORE":
      return "text-teal-300";
    case "REDUCE":
      return "text-amber-300";
    case "WAIT":
      return "text-gray-300";
    default:
      return "text-blue-200";
  }
}

export default function DailyDecisionCard({ decision }: Props) {
  return (
    <div className="relative bg-gradient-to-r from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-6 space-y-5 shadow-[0_0_40px_rgba(59,130,246,0.08)]">
      <div className="text-xs text-gray-400 uppercase tracking-wider">
        What should you do today?
      </div>

      <div>
        <p className="text-sm text-gray-400 mb-2">Today</p>
        <p className={`text-3xl font-semibold ${decisionTone(decision.decision)}`}>
          {decisionLabel(decision.decision)}
          <span className="text-lg text-gray-400 font-normal ml-3">
            ({decision.confidence}% confidence)
          </span>
        </p>
      </div>

      <div className="pt-3 border-t border-white/10">
        <div className="text-xs text-gray-400 mb-2">Why</div>
        <p className="text-sm text-gray-300 leading-relaxed">{decision.reason}</p>
        {decision.focusSymbol && decision.focusAllocationPct !== undefined && (
          <p className="text-xs text-amber-300/80 mt-2">
            Focus: {decision.focusSymbol} · {decision.focusAllocationPct}% of
            portfolio
          </p>
        )}
      </div>

      {decision.actions.length > 0 && (
        <div className="pt-3 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-2">Suggested next steps</div>
          <ul className="space-y-2">
            {decision.actions.map((action) => (
              <li key={action} className="text-sm text-gray-400">
                • {action}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
