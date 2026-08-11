"use client";

import { useEffect } from "react";
import type { SellImpact } from "@/lib/sellImpact";
import { formatInr } from "@/lib/sellImpact";
import {
  buildSellConfirmPrompt,
  type SellTrimResolution,
} from "@/lib/sellTrim";

type Props = {
  open: boolean;
  stock: string;
  impact: SellImpact;
  sellTrim?: SellTrimResolution;
  processing: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export default function SellConfirmModal({
  open,
  stock,
  impact,
  sellTrim,
  processing,
  onConfirm,
  onCancel,
}: Props) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !processing) {
        onCancel();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, processing, onCancel]);

  if (!open) {
    return null;
  }

  const confirmPrompt = sellTrim
    ? buildSellConfirmPrompt(stock, sellTrim)
    : `Sell ${impact.sellPercent}% of ${stock}?`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close"
        disabled={processing}
        onClick={onCancel}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm disabled:cursor-not-allowed"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sell-confirm-title"
        className="relative w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-5"
      >
        <div>
          <h2
            id="sell-confirm-title"
            className="text-lg font-semibold text-white"
          >
            Confirm Action
          </h2>
          <p className="text-sm text-gray-300 mt-2">{confirmPrompt}</p>
          {sellTrim?.mode === "full_exit" ? (
            <p className="text-sm text-amber-200/90 mt-2">
              A {sellTrim.requestedPercent}% trim is not possible with{" "}
              {sellTrim.holdingQty === 1
                ? "1 share"
                : `${sellTrim.holdingQty} shares`}
              . This sells your entire position.
            </p>
          ) : null}
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
          <p className="text-xs text-gray-500 uppercase tracking-wider">
            Impact
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-gray-400">Allocation</span>
              <span className="text-gray-200">
                {impact.currentAllocation}% → {impact.newAllocation}%
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-400">Risk</span>
              <span className="text-gray-200">
                {impact.currentRisk} → {impact.newRisk}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-400">Cash increase (est.)</span>
              <span className="text-emerald-300">
                +{formatInr(impact.cashIncrease)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={processing}
            onClick={onConfirm}
            className="flex-1 min-w-[140px] px-4 py-2.5 rounded-lg text-sm font-medium bg-amber-500/20 border border-amber-500/40 text-amber-100 hover:bg-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {processing ? "Processing…" : "Confirm Sell"}
          </button>
          <button
            type="button"
            disabled={processing}
            onClick={onCancel}
            className="flex-1 min-w-[100px] px-4 py-2.5 rounded-lg text-sm font-medium bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
