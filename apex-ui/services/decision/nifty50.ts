/** NIFTY 50 constituents (NSE symbols). Updated periodically via config. */
export const NIFTY_50_UNIVERSE: readonly string[] = [
  "ADANIENT",
  "ADANIPORTS",
  "APOLLOHOSP",
  "ASIANPAINT",
  "AXISBANK",
  "BAJAJ-AUTO",
  "BAJFINANCE",
  "BAJAJFINSV",
  "BPCL",
  "BHARTIARTL",
  "BRITANNIA",
  "CIPLA",
  "COALINDIA",
  "DIVISLAB",
  "DRREDDY",
  "EICHERMOT",
  "GRASIM",
  "HCLTECH",
  "HDFCBANK",
  "HDFCLIFE",
  "HEROMOTOCO",
  "HINDALCO",
  "HINDUNILVR",
  "ICICIBANK",
  "ITC",
  "INDUSINDBK",
  "INFY",
  "JSWSTEEL",
  "KOTAKBANK",
  "LT",
  "LTIM",
  "M&M",
  "MARUTI",
  "NESTLEIND",
  "NTPC",
  "ONGC",
  "POWERGRID",
  "RELIANCE",
  "SBILIFE",
  "SBIN",
  "SHRIRAMFIN",
  "SUNPHARMA",
  "TCS",
  "TATACONSUM",
  "TATAMOTORS",
  "TATASTEEL",
  "TECHM",
  "TITAN",
  "ULTRACEMCO",
  "WIPRO",
];

/** Fallback when filtering returns no candidates or market data is unavailable. */
export const FALLBACK_STOCK_UNIVERSE: readonly string[] = [
  "HDFCBANK",
  "ICICIBANK",
  "RELIANCE",
  "INFY",
  "TCS",
  "SBIN",
  "LT",
  "ITC",
];

/** @deprecated Use NIFTY_50_UNIVERSE — kept for backward compatibility. */
export const STOCK_UNIVERSE = FALLBACK_STOCK_UNIVERSE;

export function getStockUniverse(): string[] {
  return [...NIFTY_50_UNIVERSE];
}
