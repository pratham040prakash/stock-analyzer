import type { Portfolio } from "@/types/portfolio";

export const samplePortfolio: Portfolio = {
  holdings: [
    { symbol: "TCS", quantity: 10, avgPrice: 3200, currentPrice: 3500 },
    { symbol: "INFY", quantity: 15, avgPrice: 1400, currentPrice: 1500 },
    { symbol: "HDFC", quantity: 8, avgPrice: 1600, currentPrice: 1550 },
  ],
};
