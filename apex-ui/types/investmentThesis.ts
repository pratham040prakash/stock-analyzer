export type InvestmentThesisRow = {
  id: string;
  symbol: string;
  thesis: string;
  invalidation: string | null;
  updated_at: string;
};

export type InvestmentThesisInput = {
  symbol: string;
  thesis: string;
  invalidation?: string | null;
};
