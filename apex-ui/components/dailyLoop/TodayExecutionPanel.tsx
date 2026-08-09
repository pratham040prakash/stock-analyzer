"use client";

import { useCallback, useMemo, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { formatInr } from "@/lib/funds";
import type { TodayHero } from "@/lib/dailyLoop/todaySurface";
import { computeSellImpact } from "@/lib/sellImpact";
import { ApexButton } from "@/components/ui/apex";
import SellConfirmModal from "@/components/SellConfirmModal";

type ExecuteSellResponse = {
  stock: string;
  sellPercent: number;
  quantity: number;
  orderId: string;
};

type ExecuteBuyResponse = {
  stock: string;
  amount: number;
  price: number;
  quantity: number;
  orderId: string;
};

type Props = {
  hero: TodayHero;
  portfolioValue: number;
  holdingAllocationPct?: number;
  onExecuted?: () => void;
};

export default function TodayExecutionPanel({
  hero,
  portfolioValue,
  holdingAllocationPct,
  onExecuted,
}: Props) {
  const [pendingSellPercent, setPendingSellPercent] = useState<number | null>(
    null,
  );
  const [processing, setProcessing] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sellImpact = useMemo(() => {
    if (pendingSellPercent === null || !hero.symbol) {
      return null;
    }

    const allocationPct =
      holdingAllocationPct ?? hero.currentWeight ?? undefined;

    if (allocationPct === undefined) {
      return null;
    }

    return computeSellImpact(
      allocationPct,
      pendingSellPercent,
      portfolioValue,
    );
  }, [
    hero.currentWeight,
    hero.symbol,
    holdingAllocationPct,
    pendingSellPercent,
    portfolioValue,
  ]);

  const runSell = useCallback(
    async (sellPercent: number) => {
      if (!hero.symbol || processing) {
        return;
      }

      setProcessing(true);
      setError(null);
      setFeedback(null);

      try {
        const res = await apiFetch("/api/trade/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            side: "sell",
            stock: hero.symbol,
            sellPercent,
          }),
        });
        const data = await parseApiJson<ExecuteSellResponse>(res, "Sell order");

        if (!res.ok || !data) {
          setError("Could not place sell order. Check Zerodha connection.");
          return;
        }

        setFeedback(
          `Sell order placed on Zerodha · ${data.quantity} shares · order ${data.orderId}`,
        );
        setPendingSellPercent(null);
        onExecuted?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Sell order failed");
      } finally {
        setProcessing(false);
      }
    },
    [hero.symbol, onExecuted, processing],
  );

  const runBuy = useCallback(async () => {
    if (!hero.symbol || !hero.deployAmount || processing) {
      return;
    }

    setProcessing(true);
    setError(null);
    setFeedback(null);

    try {
      const res = await apiFetch("/api/trade/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          side: "buy",
          stock: hero.symbol,
          amount: hero.deployAmount,
        }),
      });
      const data = await parseApiJson<ExecuteBuyResponse>(res, "Buy order");

      if (!res.ok || !data) {
        setError("Could not place buy order. Check cash and entry rules.");
        return;
      }

      setFeedback(
        `Buy order placed on Zerodha · ${data.quantity} shares · order ${data.orderId}`,
      );
      onExecuted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Buy order failed");
    } finally {
      setProcessing(false);
    }
  }, [hero.deployAmount, hero.symbol, onExecuted, processing]);

  if (hero.executionKind === "OBSERVE") {
    return null;
  }

  if (hero.executionKind === "WAIT") {
    return (
      <div className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4 space-y-2">
        <p className="text-sm font-medium text-apex-text/90">
          No deployment today — capital stays protected.
        </p>
        <p className="text-sm text-apex-text/70">{hero.subline}</p>
      </div>
    );
  }

  if (hero.executionKind === "SELL" && hero.symbol && hero.sellPercent) {
    return (
      <>
        <div className="rounded-xl border border-apex-border/20 bg-white/[0.03] px-4 py-4 space-y-3">
          <p className="text-base font-semibold text-apex-text">
            Trim {hero.sellPercent}% of {hero.symbol}
          </p>
          <p className="text-sm text-apex-text/75">{hero.subline}</p>
          {hero.currentWeight !== undefined && hero.targetWeightAfter !== undefined ? (
            <p className="text-sm text-apex-text/70">
              Position {hero.currentWeight}% → {hero.targetWeightAfter}% after trim
            </p>
          ) : null}
          <ApexButton
            type="button"
            disabled={processing}
            onClick={() => {
              const pct = hero.sellPercent ?? null;
              if (pct === null) {
                return;
              }
              if (
                holdingAllocationPct !== undefined ||
                hero.currentWeight !== undefined
              ) {
                setPendingSellPercent(pct);
                return;
              }
              void runSell(pct);
            }}
            className="w-full sm:w-auto"
          >
            {processing ? "Placing order…" : `Confirm sell ${hero.sellPercent}% on Zerodha`}
          </ApexButton>
          {feedback ? (
            <p className="text-sm text-emerald-200/90">{feedback}</p>
          ) : null}
          {error ? <p className="text-sm text-amber-200/90">{error}</p> : null}
        </div>

        {sellImpact && hero.symbol ? (
          <SellConfirmModal
            open={pendingSellPercent !== null}
            stock={hero.symbol}
            impact={sellImpact}
            processing={processing}
            onConfirm={() => {
              if (pendingSellPercent !== null) {
                void runSell(pendingSellPercent);
              }
            }}
            onCancel={() => {
              if (!processing) {
                setPendingSellPercent(null);
              }
            }}
          />
        ) : null}
      </>
    );
  }

  if (hero.executionKind === "BUY" && hero.symbol && hero.deployAmount) {
    return (
      <div className="rounded-xl border border-apex-border/20 bg-white/[0.03] px-4 py-4 space-y-3">
        <p className="text-base font-semibold text-apex-text">
          Deploy {formatInr(hero.deployAmount)} into {hero.symbol}
        </p>
        <p className="text-sm text-apex-text/75">{hero.subline}</p>
        <p className="text-xs text-apex-muted/70">
          Stop loss and target monitoring apply after fill — confirm only if this
          matches your plan.
        </p>
        <ApexButton
          type="button"
          disabled={processing}
          onClick={() => void runBuy()}
          className="w-full sm:w-auto"
        >
          {processing ? "Placing order…" : "Confirm buy on Zerodha"}
        </ApexButton>
        {feedback ? (
          <p className="text-sm text-emerald-200/90">{feedback}</p>
        ) : null}
        {error ? <p className="text-sm text-amber-200/90">{error}</p> : null}
      </div>
    );
  }

  return null;
}
