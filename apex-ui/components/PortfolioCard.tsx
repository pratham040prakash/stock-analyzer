"use client";

import type { PortfolioHoldingRow } from "@/types/portfolioApi";

type Props = {
  holdings: PortfolioHoldingRow[];
  totalValue: number;
  totalPnl: number;
  concentrated?: boolean;
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

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

function pnlClass(pnl: number): string {
  if (pnl > 0) return "text-emerald-400";
  if (pnl < 0) return "text-red-400";
  return "text-gray-400";
}

export default function PortfolioCard({
  holdings,
  totalValue,
  totalPnl,
  concentrated,
  topSymbol,
  topAllocationPct,
}: Props) {
  if (holdings.length === 0) {
    return (
      <div className="p-6 rounded-2xl border border-white/10 bg-slate-900/50">
        <p className="text-sm text-gray-400">
          No holdings found in your Zerodha account yet.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900 to-slate-900/80 overflow-hidden shadow-[0_0_40px_rgba(59,130,246,0.06)]">
      <div className="p-6 border-b border-white/10 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">
              Your portfolio
            </p>
            <p className="text-3xl font-semibold text-white">
              {formatCurrency(totalValue)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400 mb-1">Total P&L</p>
            <p className={`text-lg font-medium ${pnlClass(totalPnl)}`}>
              {totalPnl >= 0 ? "+" : ""}
              {formatCurrency(totalPnl)}
            </p>
          </div>
        </div>

        {concentrated && topSymbol && topAllocationPct !== undefined && (
          <div className="p-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <p className="text-sm text-amber-200/90">
              ⚠️ Portfolio is highly concentrated — {topSymbol} is{" "}
              {Math.round(topAllocationPct)}% of your holdings.
            </p>
          </div>
        )}
      </div>

      <div className="divide-y divide-white/5">
        {holdings.map((holding) => (
          <div
            key={holding.tradingsymbol}
            className="px-6 py-4 grid grid-cols-2 md:grid-cols-6 gap-3 items-center"
          >
            <div className="col-span-2">
              <p className="font-medium text-white">{holding.tradingsymbol}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {Math.round(holding.allocation_pct)}% allocation
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-500">Qty</p>
              <p className="text-sm text-gray-200">{holding.quantity}</p>
            </div>

            <div>
              <p className="text-xs text-gray-500">Avg</p>
              <p className="text-sm text-gray-200">
                {formatPrice(holding.average_price)}
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-500">Current</p>
              <p className="text-sm text-gray-200">
                {formatPrice(holding.last_price)}
              </p>
            </div>

            <div className="text-right md:text-left">
              <p className="text-xs text-gray-500">P&L</p>
              <p className={`text-sm font-medium ${pnlClass(holding.pnl)}`}>
                {holding.pnl >= 0 ? "+" : ""}
                {formatCurrency(holding.pnl)}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {formatCurrency(holding.value)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
