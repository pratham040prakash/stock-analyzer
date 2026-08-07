"use client";

import { useCallback, useEffect, useState } from "react";
import type { DailyDecisionOutput, DecisionActionType } from "@/types/decision";
import {
  buildSellPercentOptions,
  decisionConfidenceBadge,
  decisionHeroActionText,
  decisionRiskMicrocopy,
} from "@/types/decision";
import { computeSellImpact } from "@/lib/sellImpact";
import ActionToast from "./ActionToast";
import SellConfirmModal from "./SellConfirmModal";

type Props = {
  decision: DailyDecisionOutput;
  totalValue?: number;
};

type ActionVisual = {
  strip: string;
  iconBg: string;
  iconText: string;
  icon: string;
  badge: string;
  primaryButton: string;
  headline: string;
};

function actionVisuals(action: DecisionActionType): ActionVisual {
  switch (action) {
    case "buy":
      return {
        strip: "bg-emerald-500",
        iconBg: "bg-emerald-500/15 border-emerald-500/30",
        iconText: "text-emerald-300",
        icon: "↑",
        badge: "bg-emerald-500/10 text-emerald-200 border-emerald-500/25",
        primaryButton:
          "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/20",
        headline: "text-emerald-50",
      };
    case "reduce":
      return {
        strip: "bg-red-500",
        iconBg: "bg-red-500/15 border-red-500/30",
        iconText: "text-red-300",
        icon: "↓",
        badge: "bg-red-500/10 text-red-100 border-red-500/25",
        primaryButton:
          "bg-red-500 hover:bg-red-400 text-white shadow-lg shadow-red-500/25",
        headline: "text-white",
      };
    case "wait":
      return {
        strip: "bg-amber-400",
        iconBg: "bg-amber-500/15 border-amber-500/30",
        iconText: "text-amber-200",
        icon: "—",
        badge: "bg-amber-500/10 text-amber-100 border-amber-500/25",
        primaryButton:
          "bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-lg shadow-amber-500/20",
        headline: "text-amber-50",
      };
    default:
      return {
        strip: "bg-amber-400",
        iconBg: "bg-amber-500/15 border-amber-500/30",
        iconText: "text-amber-200",
        icon: "—",
        badge: "bg-amber-500/10 text-amber-100 border-amber-500/25",
        primaryButton:
          "bg-slate-100 hover:bg-white text-slate-900 shadow-lg shadow-white/10",
        headline: "text-slate-50",
      };
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
  const [showAdjust, setShowAdjust] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const canTrim = decision.action === "reduce" && Boolean(decision.stock);
  const suggestedSellPercent = decision.suggested_sell_percent ?? 20;
  const sellOptions = buildSellPercentOptions(decision.suggested_sell_percent);
  const activeSellPercent = selectedSellPercent ?? suggestedSellPercent;
  const visuals = actionVisuals(decision.action);
  const heroAction = decisionHeroActionText(decision, activeSellPercent);
  const confidenceBadge = decisionConfidenceBadge(decision.confidence);
  const riskMicrocopy =
    canTrim && decision.allocation !== undefined
      ? decisionRiskMicrocopy(decision.allocation, activeSellPercent)
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
    setSelectedSellPercent(null);
    setShowAdjust(false);
    setShowReasoning(false);
  }, [decision.suggested_sell_percent, decision.stock]);

  useEffect(() => {
    if (!toastMessage) return;

    const timer = window.setTimeout(() => {
      setToastMessage(null);
    }, 3500);

    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  const openConfirm = useCallback(
    (percent: number) => {
      setSelectedSellPercent(percent);
      setPendingSellPercent(percent);
    },
    [],
  );

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
      setShowAdjust(false);
    } finally {
      setProcessing(false);
    }
  }, [pendingSellPercent, processing]);

  const primaryLabel = canTrim
    ? `Sell ${activeSellPercent}% Now`
    : decision.action === "buy"
      ? "Start investing"
      : "Got it";

  return (
    <>
      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 shadow-[0_0_60px_rgba(239,68,68,0.08)]">
        <div
          className={`absolute left-0 top-0 bottom-0 w-1.5 ${visuals.strip}`}
          aria-hidden
        />

        <div className="p-6 pl-8 space-y-6">
          <p className="text-[11px] text-gray-500 uppercase tracking-[0.2em]">
            Today&apos;s action
          </p>

          <div className="flex items-start gap-4">
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border text-xl font-semibold ${visuals.iconBg} ${visuals.iconText}`}
              aria-hidden
            >
              {visuals.icon}
            </div>

            <div className="space-y-3 min-w-0">
              <h2
                className={`text-3xl sm:text-4xl font-semibold leading-tight tracking-tight ${visuals.headline}`}
              >
                {heroAction}
              </h2>
              <span
                className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${visuals.badge}`}
              >
                {confidenceBadge}
              </span>
            </div>
          </div>

          {decision.suggestion && (
            <p className="text-sm text-gray-400">{decision.suggestion}</p>
          )}

          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                disabled={processing}
                onClick={() => {
                  if (canTrim) {
                    openConfirm(activeSellPercent);
                  }
                }}
                className={`w-full sm:flex-1 px-5 py-3.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${visuals.primaryButton}`}
              >
                {primaryLabel}
              </button>

              {canTrim && (
                <button
                  type="button"
                  disabled={processing}
                  onClick={() => setShowAdjust((open) => !open)}
                  className="w-full sm:w-auto px-5 py-3.5 rounded-xl text-sm font-medium border border-white/15 bg-white/5 text-gray-200 hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Adjust amount
                </button>
              )}
            </div>

            {riskMicrocopy && (
              <p className="text-sm text-gray-400">{riskMicrocopy}</p>
            )}

            {canTrim && showAdjust && (
              <div className="flex flex-wrap gap-2 pt-1">
                {sellOptions.map((percent) => {
                  const isActive = activeSellPercent === percent;
                  return (
                    <button
                      key={percent}
                      type="button"
                      disabled={processing}
                      onClick={() => {
                        setSelectedSellPercent(percent);
                        openConfirm(percent);
                      }}
                      className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                        isActive
                          ? "bg-red-500/20 border-red-500/40 text-red-100"
                          : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                      }`}
                    >
                      Sell {percent}%
                    </button>
                  );
                })}
              </div>
            )}

            <p className="text-xs text-gray-600">
              Guidance only — confirm to simulate; execute in your broker for
              real trades.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowReasoning((open) => !open)}
            className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            {showReasoning ? "Hide reasoning ↑" : "See reasoning →"}
          </button>

          {showReasoning && (
            <div className="space-y-4 pt-2 border-t border-white/10">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                  Why this decision?
                </p>
                {decision.confidence_factors.length > 0 ? (
                  <ul className="space-y-2">
                    {decision.confidence_factors.map((factor) => (
                      <li
                        key={factor}
                        className="text-sm text-gray-300 flex gap-2"
                      >
                        <span className="text-gray-500 shrink-0">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {decision.reason}
                  </p>
                )}
              </div>

              {decision.actions.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                    Suggested next steps
                  </p>
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
          )}
        </div>
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
