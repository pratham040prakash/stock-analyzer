"use client";

import TodayTrustStrip, {
  type TodayTrustStripProps,
} from "@/components/dailyLoop/TodayTrustStrip";
import TodayPortfolioHoldings, {
  type TodayPortfolioHoldingsProps,
} from "@/components/dailyLoop/TodayPortfolioHoldings";

export type TodayPortfolioSummaryProps = {
  trust: TodayTrustStripProps;
  holdings: TodayPortfolioHoldingsProps;
};

export default function TodayPortfolioSummary({
  trust,
  holdings,
}: TodayPortfolioSummaryProps) {
  return (
    <section className="space-y-3" aria-label="Your portfolio">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
        Your portfolio
      </p>
      <TodayTrustStrip {...trust} />
      <TodayPortfolioHoldings {...holdings} />
    </section>
  );
}
