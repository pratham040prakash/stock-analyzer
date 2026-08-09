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
import {
  ApexBody,
  ApexCard,
  ApexEyebrow,
  ApexTitle,
} from "@/components/ui/apex";

type Props = {
  onComplete?: (profile: FinancialProfile) => void;
  stepHint?: string;
};

function OptionButton({
  children,
  disabled,
  onClick,
}: {
  children: React.ReactNode;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="rounded-xl border border-apex-border bg-apex-bg px-4 py-3 text-[14px] text-apex-text transition-all duration-200 hover:bg-white/[0.03] disabled:opacity-50"
    >
      {children}
    </button>
  );
}

export default function FinancialProfileSetup({ onComplete, stepHint }: Props) {
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
    <ApexCard hover={false}>
      {stepHint ? (
        <ApexEyebrow>{stepHint}</ApexEyebrow>
      ) : null}
      <ApexBody className={stepHint ? "mt-2 italic" : "italic"}>
        Help me understand your full picture — not just your portfolio.
      </ApexBody>

      {step === "income" ? (
        <>
          <ApexTitle className="mt-4 text-[18px]">
            What&apos;s your monthly income range?
          </ApexTitle>
          <ApexEyebrow className="mt-1">
            A rough range is enough
          </ApexEyebrow>

          <div className="mt-4 grid grid-cols-2 gap-2">
            {INCOME_OPTIONS.map((option) => (
              <OptionButton
                key={option}
                onClick={() => handleIncomeSelect(option)}
              >
                {option === "<50K" ? "< ₹50K" : `₹${option}`}
              </OptionButton>
            ))}
          </div>
        </>
      ) : (
        <>
          <ApexTitle className="mt-4 text-[18px]">
            Roughly how much do you spend monthly?
          </ApexTitle>
          <ApexEyebrow className="mt-1">An estimate is fine</ApexEyebrow>

          <div className="mt-4 grid grid-cols-2 gap-2">
            {EXPENSE_OPTIONS.map((option) => (
              <OptionButton
                key={option}
                disabled={isSaving}
                onClick={() => void handleExpenseSelect(option)}
              >
                {option === "<30K" ? "< ₹30K" : `₹${option}`}
              </OptionButton>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setStep("income")}
            className="mt-4 text-[13px] text-apex-muted transition-colors hover:text-apex-text"
          >
            Back to income
          </button>
        </>
      )}

      {error ? (
        <p className="mt-4 text-[13px] text-red-300/90">{error}</p>
      ) : null}
    </ApexCard>
  );
}
