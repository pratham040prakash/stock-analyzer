"use client";

import { useCallback, useEffect, useState } from "react";
import type { DailyDecisionOutput } from "@/types/decision";
import {
  decisionAllocationHint,
  decisionHeadline,
} from "@/types/decision";
import { computeSellImpact } from "@/lib/sellImpact";
import ActionToast from "./ActionToast";
import SellConfirmModal from "./SellConfirmModal";

type Props = {
  decision: DailyDecisionOutput;
  totalValue?: number;
};

const SELL_OPTIONS = [10, 20, 50] as const;

function decisionTone(action: DailyDecisionOutput["action"]): string {
  switch (action) {
    case "buy":
      return "text-teal-300";
    case "reduce":
      return "text-amber-300";
    case "wait":
      return "text-gray-300";
    default:
      return "text-blue-200";
  }
}

export default function DailyDecisionCard({
  decision,
  totalValue = 0,
}: Props) {
  const [selectedSellPercent, setSelectedSellPercent] = useState<
    number | null
  >(null);
  const [pendingSellPercent, setPendingSellPercent] = useState<number | null>(
    null,
  );
  const [processing, setProcessing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const headline = decisionHeadline(decision);
  const canTrim = decision.action === "reduce" && Boolean(decision.stock);
  const activeSellPercent =
    selectedSellPercent ??
    decision.suggested_sell_percent ??
    SELL_OPTIONS[1];
  const allocationHint =
    canTrim && decision.allocation !== undefined
      ? decisionAllocationHint(decision.allocation, activeSellPercent)
      : null;

  const sellImpact =
    pendingSellPercent !== null &&
    decision.stock &&
    decision.allocation !== undefined
      ? computeSellImpact(
          decision.allocation,
          pendingSellPercent,
          totalValue,
        )
      : null;

  useEffect(() => {
    if (!toastMessage) return;

    const timer = window.setTimeout(() => {
      setToastMessage(null);
    }, 3500);

    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  const handleSellClick = useCallback((percent: number) => {
    setSelectedSellPercent(percent);
    setPendingSellPercent(percent);
  }, []);

  const handleCancel = useCallback(() => {
    if (processing) return;
    setPendingSellPercent(null);
  }, [processing]);

  const handleConfirm = useCallback(async () => {
    if (processing || pendingSellPercent === null) return;

    setProcessing(true);
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 1400));
      setToastMessage("Order placed successfully");
      setPendingSellPercent(null);
    } finally {
      setProcessing(false);
    }
  }, [pendingSellPercent, processing]);

  return (
    <>
      <div className="relative bg-gradient-to-r from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-6 space-y-5 shadow-[0_0_40px_rgba(59,130,246,0.08)]">
        <div className="text-xs text-gray-400 uppercase tracking-wider">
          What should you do today?
        </div>

        <div>
          <p className="text-sm text-gray-400 mb-2">Today</p>
          <p
            className={`text-3xl font-semibold ${decisionTone(decision.action)}`}
          >
            {headline}
          </p>
          {decision.suggestion && (
            <p className="text-xs uppercase tracking-wider text-amber-400/80 mt-2">
              {decision.suggestion}
            </p>
          )}
          {decision.message && (
            <p className="text-sm text-gray-300 mt-3 leading-relaxed">
              {decision.message}
            </p>
          )}
        </div>

        {canTrim && (
          <>
            <div className="flex flex-wrap gap-2">
              {SELL_OPTIONS.map((percent) => {
                const isActive = activeSellPercent === percent;
                return (
                  <button
                    key={percent}
                    type="button"
                    disabled={processing}
                    onClick={() => handleSellClick(percent)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      isActive
                        ? "bg-amber-500/20 border-amber-500/40 text-amber-100"
                        : "bg-amber-500/10 border-amber-500/30 text-amber-200 hover:bg-amber-500/20"
                    }`}
                  >
                    Sell {percent}%
                  </button>
                );
              })}
            </div>

            {allocationHint && (
              <div className="p-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
                <p className="text-sm text-amber-100/90">{allocationHint}</p>
                <p className="text-xs text-gray-500 mt-2">
                  Guidance only — confirm to simulate; execute in your broker
                  for real trades.
                </p>
              </div>
            )}
          </>
        )}

        <div className="pt-3 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-2">Why this decision?</div>
          {decision.confidence_factors.length > 0 ? (
            <ul className="space-y-2">
              {decision.confidence_factors.map((factor) => (
                <li key={factor} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-amber-400/70 shrink-0">•</span>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-300 leading-relaxed">
              {decision.reason}
            </p>
          )}
          {decision.stock && decision.allocation !== undefined && (
            <p className="text-xs text-amber-300/80 mt-3">
              {decision.confidence}% confidence · {decision.stock} ·{" "}
              {decision.allocation}% allocation
            </p>
          )}
        </div>

        {!canTrim && decision.actions.length > 0 && (
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

      {decision.stock && sellImpact && (
        <SellConfirmModal
          open={pendingSellPercent !== null}
          stock={decision.stock}
          impact={sellImpact}
          processing={processing}
          onConfirm={() => void handleConfirm()}
          onCancel={handleCancel}
        />
      )}

      <ActionToast message={toastMessage} />
    </>
  );
}
