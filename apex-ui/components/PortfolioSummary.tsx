"use client";

import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import { ApexCard, ApexRow } from "@/components/ui/apex";

type Props = {
  totalValue: number;
  dayPnl: number | null;
  riskScore: number;
  riskLevel: PortfolioRiskLevel;
  topSymbol?: string;
  topAllocationPct?: number;
  stale?: boolean;
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
    return "text-apex-muted";
  }
  if (dayPnl > 0) {
    return "text-emerald-400";
  }
  if (dayPnl < 0) {
    return "text-red-400";
  }
  return "text-apex-muted";
}

export default function PortfolioSummary({
  totalValue,
  dayPnl,
  stale = false,
}: Props) {
  return (
    <ApexCard hover={false} padding="compact">
      {stale ? (
        <p className="mb-3 text-xs text-amber-200/90">
          Session expired · portfolio values may be stale.{" "}
          <a
            href="/api/zerodha/login"
            className="underline underline-offset-2 hover:text-amber-100"
          >
            Reconnect Zerodha
          </a>
        </p>
      ) : null}
      <ApexRow label="Portfolio" value={formatCurrency(totalValue)} />
      <ApexRow
        label="Today"
        value={formatDayPnl(dayPnl)}
        valueClassName={dayPnlClass(dayPnl)}
      />
    </ApexCard>
  );
}

export function PortfolioSummarySkeleton() {
  return (
    <ApexCard hover={false} padding="compact">
      <div className="space-y-4">
        <div className="h-4 w-full rounded bg-white/10 animate-pulse" />
        <div className="h-4 w-full rounded bg-white/10 animate-pulse" />
      </div>
    </ApexCard>
  );
}
