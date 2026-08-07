"use client";

import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";

type Props = {
  totalValue: number;
  dayPnl: number | null;
  riskScore: number;
  riskLevel: PortfolioRiskLevel;
  topSymbol?: string;
  topAllocationPct?: number;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDayPnl(dayPnl: number | null): string {
  if (dayPnl === null) {
    return "—";
  }
  if (dayPnl === 0) {
    return "₹0";
  }
  const formatted = formatCurrency(Math.abs(dayPnl));
  return dayPnl > 0 ? `+${formatted}` : `-${formatted}`;
}

function dayPnlClass(dayPnl: number | null): string {
  if (dayPnl === null) {
    return "text-gray-300";
  }
  if (dayPnl > 0) {
    return "text-emerald-400";
  }
  if (dayPnl < 0) {
    return "text-red-400";
  }
  return "text-gray-300";
}

function riskIndicator(level: PortfolioRiskLevel): string {
  switch (level) {
    case "High":
      return "🔴";
    case "Medium":
      return "🟡";
    default:
      return "🟢";
  }
}

function SummaryItem({
  label,
  value,
  valueClassName = "text-white",
}: {
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className={`text-xl font-semibold ${valueClassName}`}>{value}</p>
    </div>
  );
}

export default function PortfolioSummary({
  totalValue,
  dayPnl,
  riskScore,
  riskLevel,
  topSymbol,
  topAllocationPct,
}: Props) {
  const topHolding =
    topSymbol && topAllocationPct !== undefined
      ? `${topSymbol} ${Math.round(topAllocationPct)}%`
      : "—";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <SummaryItem
        label="Total Value"
        value={formatCurrency(totalValue)}
      />
      <SummaryItem
        label="Today's P&L"
        value={formatDayPnl(dayPnl)}
        valueClassName={dayPnlClass(dayPnl)}
      />
      <SummaryItem
        label="Risk Score"
        value={`${riskScore}/10 ${riskIndicator(riskLevel)}`}
        valueClassName={
          riskLevel === "High"
            ? "text-amber-300"
            : riskLevel === "Medium"
              ? "text-yellow-300"
              : "text-teal-300"
        }
      />
      <SummaryItem label="Top Holding" value={topHolding} />
    </div>
  );
}

export function PortfolioSummarySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-2"
        >
          <div className="h-3 w-16 rounded bg-white/10 animate-pulse" />
          <div className="h-6 w-20 rounded bg-white/10 animate-pulse" />
        </div>
      ))}
    </div>
  );
}
