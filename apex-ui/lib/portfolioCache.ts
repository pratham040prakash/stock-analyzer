import type { Portfolio } from "@/types/portfolio";

const CACHE_KEY = "portfolio_cache";
const VISIT_KEY = "apex_visit_count";

const listeners = new Set<() => void>();

function notifyListeners() {
  listeners.forEach((listener) => listener());
}

export function subscribePortfolioCache(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getCachedPortfolioSnapshot(): Portfolio | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Portfolio;
  } catch {
    return null;
  }
}

export function saveCachedPortfolio(portfolio: Portfolio) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CACHE_KEY, JSON.stringify(portfolio));
  notifyListeners();
}

export function getVisitCount(): number {
  if (typeof window === "undefined") return 0;
  return Number(localStorage.getItem(VISIT_KEY) ?? 0);
}

export function recordVisit(): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(VISIT_KEY, String(getVisitCount() + 1));
}
