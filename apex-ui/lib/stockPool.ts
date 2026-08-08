export type StockSector =
  | "ETF"
  | "Banking"
  | "IT"
  | "Energy"
  | "Auto"
  | "FMCG"
  | "Pharma"
  | "Infrastructure"
  | "Financial Services";

export type StockCap = "etf" | "large" | "mid";

export type StockProfile = {
  name: string;
  symbol: string;
  sector: StockSector;
  cap: StockCap;
  stability: number;
  growth: number;
  type: string;
  reason: string;
};

export const STOCK_POOL: StockProfile[] = [
  {
    name: "NIFTYBEES",
    symbol: "NIFTYBEES",
    sector: "ETF",
    cap: "etf",
    stability: 10,
    growth: 5,
    type: "ETF",
    reason: "Broad market diversification",
  },
  {
    name: "HDFC Bank",
    symbol: "HDFCBANK",
    sector: "Banking",
    cap: "large",
    stability: 9,
    growth: 6,
    type: "Large Cap",
    reason: "Stable banking leader",
  },
  {
    name: "ICICI Bank",
    symbol: "ICICIBANK",
    sector: "Banking",
    cap: "large",
    stability: 8,
    growth: 7,
    type: "Large Cap",
    reason: "Quality private bank",
  },
  {
    name: "Infosys",
    symbol: "INFY",
    sector: "IT",
    cap: "large",
    stability: 8,
    growth: 7,
    type: "IT Leader",
    reason: "Consistent IT compounder",
  },
  {
    name: "TCS",
    symbol: "TCS",
    sector: "IT",
    cap: "large",
    stability: 9,
    growth: 6,
    type: "Large Cap",
    reason: "Defensive IT anchor",
  },
  {
    name: "Reliance",
    symbol: "RELIANCE",
    sector: "Energy",
    cap: "large",
    stability: 7,
    growth: 8,
    type: "Market Leader",
    reason: "Diversified energy leader",
  },
  {
    name: "Tata Motors",
    symbol: "TATAMOTORS",
    sector: "Auto",
    cap: "large",
    stability: 6,
    growth: 9,
    type: "Momentum",
    reason: "EV and export tailwinds",
  },
  {
    name: "Asian Paints",
    symbol: "ASIANPAINT",
    sector: "FMCG",
    cap: "large",
    stability: 9,
    growth: 5,
    type: "Defensive",
    reason: "Steady consumer franchise",
  },
  {
    name: "Sun Pharma",
    symbol: "SUNPHARMA",
    sector: "Pharma",
    cap: "large",
    stability: 8,
    growth: 6,
    type: "Pharma",
    reason: "Healthcare diversification",
  },
  {
    name: "L&T",
    symbol: "LT",
    sector: "Infrastructure",
    cap: "large",
    stability: 7,
    growth: 7,
    type: "Infrastructure",
    reason: "Capital goods exposure",
  },
  {
    name: "Bajaj Finance",
    symbol: "BAJFINANCE",
    sector: "Financial Services",
    cap: "large",
    stability: 7,
    growth: 8,
    type: "Growth",
    reason: "NBFC growth leader",
  },
  {
    name: "HUL",
    symbol: "HINDUNILVR",
    sector: "FMCG",
    cap: "large",
    stability: 9,
    growth: 5,
    type: "Defensive",
    reason: "Recession-resilient FMCG",
  },
  {
    name: "Axis Bank",
    symbol: "AXISBANK",
    sector: "Banking",
    cap: "large",
    stability: 7,
    growth: 7,
    type: "Large Cap",
    reason: "Turnaround private bank",
  },
  {
    name: "Maruti",
    symbol: "MARUTI",
    sector: "Auto",
    cap: "large",
    stability: 8,
    growth: 6,
    type: "Auto Leader",
    reason: "Passenger market leader",
  },
  {
    name: "NTPC",
    symbol: "NTPC",
    sector: "Energy",
    cap: "large",
    stability: 8,
    growth: 5,
    type: "Utility",
    reason: "Stable power utility",
  },
  {
    name: "Wipro",
    symbol: "WIPRO",
    sector: "IT",
    cap: "large",
    stability: 7,
    growth: 6,
    type: "IT Value",
    reason: "Value IT exposure",
  },
  {
    name: "Persistent",
    symbol: "PERSISTENT",
    sector: "IT",
    cap: "mid",
    stability: 6,
    growth: 9,
    type: "Mid Cap IT",
    reason: "Higher-growth IT name",
  },
  {
    name: "Divi's Labs",
    symbol: "DIVISLAB",
    sector: "Pharma",
    cap: "large",
    stability: 8,
    growth: 7,
    type: "Pharma Growth",
    reason: "API export leader",
  },
];

const SYMBOL_SECTOR_OVERRIDES: Record<string, StockSector> = {
  JIOFIN: "Financial Services",
  SBIN: "Banking",
  KOTAKBANK: "Banking",
  ITC: "FMCG",
  BHARTIARTL: "Infrastructure",
};

export function normalizeSymbol(symbol: string): string {
  return symbol.toUpperCase().replace(/[^A-Z0-9]/g, "");
}

export function sectorForSymbol(symbol: string | undefined): StockSector | null {
  if (!symbol) {
    return null;
  }

  const normalized = normalizeSymbol(symbol);
  const fromPool = STOCK_POOL.find((stock) => stock.symbol === normalized);
  if (fromPool) {
    return fromPool.sector;
  }

  return SYMBOL_SECTOR_OVERRIDES[normalized] ?? null;
}
