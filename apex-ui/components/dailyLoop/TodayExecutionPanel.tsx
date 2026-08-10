"use client";

import { useCallback, useMemo, useState } from "react";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { apiFetch, parseApiJson, readTradeExecutionError } from "@/lib/api/clientFetch";
import { formatInr } from "@/lib/funds";
import { getMarketOrderBlockReason } from "@/lib/broker/marketSession";
import type { TodayHero } from "@/lib/dailyLoop/todaySurface";
import { computeSellImpact } from "@/lib/sellImpact";
import type { ExecutionPlanSafeOutput } from "@/services/execution/executionPlanEngine";
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
  stopLoss?: number;
  stopLossOrderId?: string;
  stopLossNote?: string;
};

type ApiErrorBody = {
  status?: string;
  message?: string;
};

type Props = {
  hero: TodayHero;
  portfolioValue: number;
  holdingAllocationPct?: number;
  entryTiming?: EntryTimingState;
  plan?: ExecutionPlanSafeOutput | null;
  planLoading?: boolean;
  onExecuted?: () => void;
};

function PlanStepRow({ index, text }: { index: number; text: string }) {
  return (
    <li className="flex items-start gap-2 text-sm leading-snug text-apex-text/80">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-apex-border/30 text-[10px] font-semibold text-apex-muted">
        {index}
      </span>
      <span>{text}</span>
    </li>
  );
}

function TradeErrorNotice({
  message,
  showReconnect,
}: {
  message: string;
  showReconnect: boolean;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-amber-200/90">{message}</p>
      {showReconnect ? (
        <a
          href="/api/zerodha/login"
          className="inline-flex text-sm font-medium text-blue-200 underline underline-offset-2"
        >
          Reconnect Zerodha
        </a>
      ) : null}
    </div>
  );
}

export default function TodayExecutionPanel({
  hero,
  portfolioValue,
  holdingAllocationPct,
  entryTiming,
  plan,
  planLoading = false,
  onExecuted,
}: Props) {
  const [pendingSellPercent, setPendingSellPercent] = useState<number | null>(
    null,
  );
  const [processing, setProcessing] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsZerodhaReconnect, setNeedsZerodhaReconnect] = useState(false);

  const canEnter = entryTiming?.enter ?? true;
  const marketBlockReason = getMarketOrderBlockReason();
  const canPlaceMarketOrder = marketBlockReason === null;

  const targetFromPlan = useMemo(() => {
    if (!plan?.steps.length) {
      return null;
    }

    for (const step of plan.steps) {
      const breakoutMatch = step.match(/breakout above ([₹,\d]+)/i);
      if (breakoutMatch?.[1]) {
        return breakoutMatch[1];
      }
    }

    return null;
  }, [plan?.steps]);

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
      setNeedsZerodhaReconnect(false);
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
        const data = await parseApiJson<ExecuteSellResponse & ApiErrorBody>(
          res,
          "Sell order",
        );

        if (!res.ok || !data?.orderId) {
          const tradeError = readTradeExecutionError(
            res,
            data,
            "Could not place sell order. Check Zerodha connection.",
          );
          setError(tradeError.message);
          setNeedsZerodhaReconnect(tradeError.needsZerodhaReconnect);
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
    if (!hero.symbol || !hero.deployAmount || processing || !canEnter) {
      return;
    }

    setProcessing(true);
    setError(null);
    setNeedsZerodhaReconnect(false);
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
      const data = await parseApiJson<ExecuteBuyResponse & ApiErrorBody>(
        res,
        "Buy order",
      );

      if (!res.ok || !data?.orderId) {
        const tradeError = readTradeExecutionError(
          res,
          data,
          "Could not place buy order. Check cash and entry rules.",
        );
        setError(tradeError.message);
        setNeedsZerodhaReconnect(tradeError.needsZerodhaReconnect);
        return;
      }

      const stopNote = data.stopLossNote
        ? ` ${data.stopLossNote}`
        : plan?.stopLoss !== null && plan?.stopLoss !== undefined
          ? ` Stop monitoring from ${formatInr(plan.stopLoss)}.`
          : "";

      setFeedback(
        `Buy order placed on Zerodha · ${data.quantity} shares · order ${data.orderId}.${stopNote}`,
      );
      onExecuted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Buy order failed");
    } finally {
      setProcessing(false);
    }
  }, [canEnter, hero.deployAmount, hero.symbol, onExecuted, plan?.stopLoss, processing]);

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
          {marketBlockReason ? (
            <p className="text-sm text-amber-200/90">{marketBlockReason}</p>
          ) : (
            <p className="text-xs text-apex-muted/65">
              Stop loss and staged targets apply on buy setups. Today is a trim-only
              action.
            </p>
          )}
          <ApexButton
            type="button"
            disabled={processing || !canPlaceMarketOrder}
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
          {error ? (
            <TradeErrorNotice
              message={error}
              showReconnect={needsZerodhaReconnect}
            />
          ) : null}
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
      <div className="rounded-xl border border-apex-border/20 bg-white/[0.03] px-4 py-4 space-y-4">
        <div>
          <p className="text-base font-semibold text-apex-text">
            Deploy {formatInr(hero.deployAmount)} into {hero.symbol}
          </p>
          <p className="mt-1 text-sm text-apex-text/75">{hero.subline}</p>
        </div>

        {entryTiming ? (
          <div
            className={[
              "rounded-lg border px-3 py-2.5 text-sm",
              canEnter
                ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-200/95"
                : "border-amber-500/20 bg-amber-500/5 text-amber-100/95",
            ].join(" ")}
          >
            {canEnter
              ? "Entry conditions confirmed — you may proceed with the plan"
              : entryTiming.reason || "Waiting for entry confirmation"}
          </div>
        ) : null}

        <section className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Risk plan
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-2.5">
              <p className="text-[11px] uppercase tracking-wide text-apex-muted">
                Stop loss
              </p>
              <p className="mt-1 text-sm font-medium text-apex-text">
                {plan?.stopLoss !== null && plan?.stopLoss !== undefined
                  ? formatInr(plan.stopLoss)
                  : "Set after entry"}
              </p>
            </div>
            <div className="rounded-lg border border-apex-border/15 bg-white/[0.02] px-3 py-2.5">
              <p className="text-[11px] uppercase tracking-wide text-apex-muted">
                Target zone
              </p>
              <p className="mt-1 text-sm font-medium text-apex-text">
                {targetFromPlan ? `Breakout above ${targetFromPlan}` : "Staged in plan steps"}
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Execution plan
          </p>
          {planLoading ? (
            <p className="text-sm text-apex-muted/70">Building your plan…</p>
          ) : plan && plan.steps.length > 0 ? (
            <>
              {plan.stopLoss !== null ? (
                <p className="text-sm text-apex-text/80">
                  Stop loss: {formatInr(plan.stopLoss)} · Target: staged adds in
                  plan steps below
                </p>
              ) : null}
              <ol className="space-y-2">
                {plan.steps.map((step, index) => (
                  <PlanStepRow key={step} index={index + 1} text={step} />
                ))}
              </ol>
              {plan.riskNote ? (
                <p className="text-xs text-apex-muted/75">{plan.riskNote}</p>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-apex-muted/70">
              Plan unavailable — review entry rules before buying.
            </p>
          )}
        </section>

        <p className="text-xs text-apex-muted/70">
          Confirm buy places the entry on Zerodha and attempts a protective stop-loss
          sell order. Staged targets stay in the plan below — verify all orders in
          Zerodha.
        </p>
        {marketBlockReason ? (
          <p className="text-sm text-amber-200/90">{marketBlockReason}</p>
        ) : null}
        <ApexButton
          type="button"
          disabled={processing || !canEnter || !canPlaceMarketOrder}
          onClick={() => void runBuy()}
          className="w-full sm:w-auto"
        >
          {processing
            ? "Placing order…"
            : canEnter
              ? "Confirm buy on Zerodha"
              : "Entry not confirmed yet"}
        </ApexButton>

        {feedback ? (
          <p className="text-sm text-emerald-200/90">{feedback}</p>
        ) : null}
        {error ? (
          <TradeErrorNotice
            message={error}
            showReconnect={needsZerodhaReconnect}
          />
        ) : null}
      </div>
    );
  }

  return null;
}
