"use client";

import { useState } from "react";
import {
  EXPENSE_OPTIONS,
  INCOME_OPTIONS,
  type ExpenseRange,
  type FinancialProfile,
  type IncomeRange,
} from "@/lib/financialProfile";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

type Props = {
  onComplete?: (profile: FinancialProfile) => void;
};

export default function FinancialProfileSetup({ onComplete }: Props) {
  const [step, setStep] = useState<"income" | "expense">("income");
  const [incomeRange, setIncomeRange] = useState<IncomeRange | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleIncomeSelect(range: IncomeRange) {
    setIncomeRange(range);
    setStep("expense");
  }

  async function handleExpenseSelect(range: ExpenseRange) {
    if (!incomeRange) return;

    const profile: FinancialProfile = {
      incomeRange,
      expenseRange: range,
    };

    setIsSaving(true);
    setError(null);

    try {
      const res = await apiFetch("/api/financial-profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });

      const data = await parseApiJson<{ error?: string; message?: string }>(
        res,
        "Financial profile",
      );

      if (!res.ok) {
        throw new Error(data?.error ?? data?.message ?? "Could not save profile");
      }

      if (!data) {
        throw new Error("Could not save profile");
      }

      onComplete?.(profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="p-6 rounded-2xl border border-white/10 bg-slate-900/50 space-y-4">
      <p className="text-sm text-gray-400 italic">
        I&apos;m trying to understand your full picture — not just your
        portfolio.
      </p>

      {step === "income" ? (
        <>
          <div>
            <h2 className="text-lg font-medium text-white mb-1">
              What&apos;s your monthly income range?
            </h2>
            <p className="text-xs text-gray-500">
              A rough range is enough — saved securely to your account.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {INCOME_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => handleIncomeSelect(option)}
                className="px-4 py-3 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 text-sm text-gray-200 transition-all active:scale-95"
              >
                {option === "<50K" ? "< ₹50K" : `₹${option}`}
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <div>
            <h2 className="text-lg font-medium text-white mb-1">
              Roughly how much do you spend monthly?
            </h2>
            <p className="text-xs text-gray-500">
              Include rent, bills, and everyday spending — an estimate is fine.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {EXPENSE_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                disabled={isSaving}
                onClick={() => void handleExpenseSelect(option)}
                className="px-4 py-3 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 disabled:opacity-50 text-sm text-gray-200 transition-all active:scale-95"
              >
                {option === "<30K" ? "< ₹30K" : `₹${option}`}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setStep("income")}
            className="text-xs text-gray-500 hover:text-gray-400"
          >
            ← Back to income
          </button>
        </>
      )}

      {error && <p className="text-sm text-red-300/90">{error}</p>}
    </div>
  );
}
