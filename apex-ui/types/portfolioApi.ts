export type PortfolioHoldingRow = {
  tradingsymbol: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
  value: number;
  allocation_pct: number;
};

export type PortfolioApiResponse = {
  status: "OK" | "NOT_CONNECTED" | "TOKEN_EXPIRED" | "ERROR";
  holdings: PortfolioHoldingRow[];
  total_value?: number;
  total_pnl?: number;
  day_pnl?: number | null;
  /** Zerodha Positions tab total — (LTP − avg) × qty incl. sold legs. */
  positions_pnl?: number | null;
  /** Dashboard day move vs prior close — not Open P&L. */
  portfolio_day_pnl?: number | null;
  concentrated?: boolean;
  top_symbol?: string;
  top_allocation_pct?: number;
  risk_score?: number;
  risk_level?: "High" | "Medium" | "Low";
  message?: string;
  stale?: boolean;
};
