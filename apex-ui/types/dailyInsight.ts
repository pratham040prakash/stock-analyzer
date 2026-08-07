export type MarketTrendKind =
  | "bullish"
  | "slightly_bullish"
  | "neutral"
  | "slightly_bearish"
  | "bearish";

export type DailyInsight = {
  day_pnl: number | null;
  market_trend: MarketTrendKind;
  market_label: string;
  guidance: string;
  pnl_line: string;
};
