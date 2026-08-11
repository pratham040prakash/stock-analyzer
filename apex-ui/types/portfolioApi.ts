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
  /** Day move vs prior close (Zerodha holdings day P&L footer). Not Open P&L. */
  day_pnl?: number | null;
  /** Zerodha Positions tab total — (LTP − avg) × qty incl. sold legs. */
  positions_pnl?: number | null;
  /** Same as day_pnl when live — kept for backward-compatible clients. */
  portfolio_day_pnl?: number | null;
  concentrated?: boolean;
  top_symbol?: string;
  top_allocation_pct?: number;
  risk_score?: number;
  risk_level?: "High" | "Medium" | "Low";
  message?: string;
  stale?: boolean;
};
