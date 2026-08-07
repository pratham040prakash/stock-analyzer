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
  concentrated?: boolean;
  top_symbol?: string;
  top_allocation_pct?: number;
  message?: string;
  stale?: boolean;
};
