import type { Portfolio } from "@/types/portfolio";

export type IncomeRange = "<50K" | "50K-1L" | "1L-2L" | "2L+";
export type ExpenseRange = "<30K" | "30K-50K" | "50K-1L" | "1L+";

export type FinancialProfile = {
  incomeRange: IncomeRange;
  expenseRange: ExpenseRange;
};

export const INCOME_OPTIONS: IncomeRange[] = [
  "<50K",
  "50K-1L",
  "1L-2L",
  "2L+",
];

export const EXPENSE_OPTIONS: ExpenseRange[] = [
  "<30K",
  "30K-50K",
  "50K-1L",
  "1L+",
];

const STORAGE_KEY = "apex_financial_profile";
const listeners = new Set<() => void>();

function notifyListeners() {
  listeners.forEach((listener) => listener());
}

export function subscribeFinancialProfile(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getFinancialProfileSnapshot(): FinancialProfile | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as FinancialProfile;
  } catch {
    return null;
  }
}

export function saveFinancialProfile(profile: FinancialProfile) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  notifyListeners();
}

export function isProfileComplete(
  profile: FinancialProfile | null,
): profile is FinancialProfile {
  return Boolean(profile?.incomeRange && profile?.expenseRange);
}

const INCOME_MIDPOINTS: Record<IncomeRange, number> = {
  "<50K": 40000,
  "50K-1L": 75000,
  "1L-2L": 150000,
  "2L+": 250000,
};

const EXPENSE_MIDPOINTS: Record<ExpenseRange, number> = {
  "<30K": 20000,
  "30K-50K": 40000,
  "50K-1L": 70000,
  "1L+": 120000,
};

export function getIncomeMidpoint(range: IncomeRange): number {
  return INCOME_MIDPOINTS[range];
}

export function getExpenseMidpoint(range: ExpenseRange): number {
  return EXPENSE_MIDPOINTS[range];
}

export function getInvestableSurplus(profile: FinancialProfile): number {
  const surplus =
    getIncomeMidpoint(profile.incomeRange) -
    getExpenseMidpoint(profile.expenseRange);
  return Math.max(0, surplus);
}

export function formatRupee(amount: number): string {
  const rounded = Math.round(amount / 1000) * 1000;
  return `₹${rounded.toLocaleString("en-IN")}`;
}

export type AllocationLevel = "low" | "high" | "neutral";

export function getPortfolioAllocationLevel(
  portfolio: Portfolio,
  monthlySurplus: number,
): AllocationLevel {
  if (monthlySurplus <= 0) return "neutral";

  const totalInvested = portfolio.holdings.reduce(
    (sum, h) => sum + h.avgPrice * h.quantity,
    0,
  );

  if (totalInvested === 0) return "low";

  const yearOfSurplusInPortfolio = totalInvested / (monthlySurplus * 12);

  if (yearOfSurplusInPortfolio < 0.75) return "low";
  return "high";
}
