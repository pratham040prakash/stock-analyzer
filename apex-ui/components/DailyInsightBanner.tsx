"use client";

import type { DailyInsight } from "@/types/dailyInsight";

type Props = {
  insight: DailyInsight;
};

function pnlClass(dayPnl: number | null): string {
  if (dayPnl === null) {
    return "text-gray-300";
  }
  if (dayPnl > 0) {
    return "text-emerald-300";
  }
  if (dayPnl < 0) {
    return "text-red-300";
  }
  return "text-gray-300";
}

function marketClass(trend: DailyInsight["market_trend"]): string {
  switch (trend) {
    case "bullish":
    case "slightly_bullish":
      return "text-teal-300";
    case "bearish":
    case "slightly_bearish":
      return "text-amber-300";
    default:
      return "text-gray-300";
  }
}

export default function DailyInsightBanner({ insight }: Props) {
  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800 p-5 shadow-[0_0_40px_rgba(59,130,246,0.06)]">
      <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">
        Today
      </p>
      <div className="space-y-2">
        <p className={`text-lg font-medium ${pnlClass(insight.day_pnl)}`}>
          {insight.pnl_line}
        </p>
        <p className={`text-sm ${marketClass(insight.market_trend)}`}>
          {insight.market_label}
        </p>
        <p className="text-sm text-gray-300 leading-relaxed">
          {insight.guidance}
        </p>
      </div>
    </div>
  );
}
