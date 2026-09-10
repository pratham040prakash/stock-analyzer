"use client";

import Link from "next/link";
import { formatInr } from "@/lib/funds";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";

function formatLast(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}
import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";
import type { AllocationBucket } from "@/services/portfolio/allocationPolicy";

type Props = {
  holding: PortfolioHoldingRow;
  health?: HoldingHealthChip;
  bucket?: AllocationBucket;
};

function toneClass(value: number | null): string {
  if (value === null || Math.abs(value) < 0.5) {
    return "text-apex-text";
  }

  return value > 0 ? "text-emerald-200" : "text-rose-200";
}

function healthClass(grade?: HoldingHealthChip["grade"]): string {
  if (grade === "Strong") {
    return "border-emerald-400/25 bg-emerald-400/10 text-emerald-100";
  }

  if (grade === "Watch") {
    return "border-amber-400/25 bg-amber-400/10 text-amber-100";
  }

  if (grade === "Risk") {
    return "border-rose-400/25 bg-rose-400/10 text-rose-100";
  }

  return "border-white/10 bg-white/[0.06] text-apex-text";
}

function lastMarkPercent(pct: number | null): number {
  if (pct === null || !Number.isFinite(pct)) {
    return 50;
  }

  return Math.max(8, Math.min(92, 50 + pct * 8));
}

export default function PortfolioHoldingCard({ holding, health, bucket }: Props) {
  const shares =
    holding.quantity === 1 ? "1 share" : `${Math.round(holding.quantity)} shares`;
  const hasAvg = Number.isFinite(holding.average_price) && holding.average_price > 0;
  const hasLast = Number.isFinite(holding.last_price) && holding.last_price > 0;
  const vsBuyInr = hasAvg && hasLast ? holding.last_price - holding.average_price : null;
  const vsBuyPct =
    vsBuyInr !== null && hasAvg ? (vsBuyInr / holding.average_price) * 100 : null;
  const vsBuyLabel =
    vsBuyInr === null
      ? null
      : Math.abs(vsBuyInr) < 0.5
        ? "At your buy"
        : vsBuyInr > 0
          ? `${formatInr(vsBuyInr)} above your buy`
          : `${formatInr(Math.abs(vsBuyInr))} below your buy`;
  const mark = lastMarkPercent(vsBuyPct);

  return (
    <article className="relative overflow-hidden rounded-[28px] border border-white/[0.08] bg-gradient-to-b from-sky-400/[0.08] to-transparent px-5 py-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(52,211,153,0.10),transparent_42%)]" />

      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-apex-muted/70">
            {holding.tradingsymbol}
          </p>
          <p className="mt-1 text-sm text-apex-muted/85">
            {shares}
            {bucket ? ` · ${bucket}` : ""}
          </p>
        </div>
        {health ? (
          <p
            className={`rounded-full border px-3 py-1 text-[11px] font-medium ${healthClass(health.grade)}`}
          >
            {health.grade}
          </p>
        ) : null}
      </div>

      <div className="relative mt-5 text-center">
        {hasLast ? (
          <p className={`text-4xl font-semibold tracking-tight ${toneClass(vsBuyInr)}`}>
            {formatLast(holding.last_price)}
          </p>
        ) : (
          <p className="text-lg font-medium text-apex-text">
            {formatInr(holding.value)}
          </p>
        )}
        {vsBuyLabel ? (
          <p className={`mt-2 text-sm ${toneClass(vsBuyInr)}`}>{vsBuyLabel}</p>
        ) : null}
      </div>

      <div className="relative mt-5">
        <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.08]">
          <div
            className="h-full w-1.5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.35)]"
            style={{ marginLeft: `calc(${mark}% - 3px)` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between gap-3 text-xs text-apex-muted/80">
          <span>{hasAvg ? `Avg ${formatLast(holding.average_price)}` : "Your buy"}</span>
          <span>{formatInr(holding.value)}</span>
          <span>{Math.round(holding.allocation_pct)}%</span>
        </div>
      </div>

      <Link
        href={`/app/research?symbol=${encodeURIComponent(holding.tradingsymbol)}`}
        className="relative mt-4 inline-flex text-xs text-apex-muted/70 underline-offset-2 hover:text-apex-text hover:underline"
      >
        Research →
      </Link>
    </article>
  );
}
