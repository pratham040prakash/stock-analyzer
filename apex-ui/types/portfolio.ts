export type Holding = {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  closePrice?: number;
  /** Per-share day change from Zerodha holdings, when available. */
  dayChange?: number;
};

export type Portfolio = {
  holdings: Holding[];
};

export type Insight = {
  type: "concentration" | "performance" | "action";
  message: string;
  severity: "low" | "medium" | "high";
};

export type Decision = {
  stance: "BUY" | "SELL" | "HOLD" | "WAIT";
  confidence: string;
  takeaway: string;
};

export type StockAnalysis = {
  symbol: string;
  trend: "up" | "down" | "sideways";
  valuation: "cheap" | "fair" | "expensive";
  strength: "strong" | "weak";
  decision: "BUY" | "SELL" | "HOLD";
  reasoning: string;
  confidence: "low" | "medium" | "high";
  priority: number;
};
