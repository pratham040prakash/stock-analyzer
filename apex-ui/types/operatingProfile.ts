export type InvestmentStyle =
  | "long_term_only"
  | "core_plus_tactical"
  | "tactical_only";

export type OperatingProfile = {
  investmentStyle: InvestmentStyle;
  intradayAcknowledgedAt: string;
};

export function parseInvestmentStyle(value: unknown): InvestmentStyle | null {
  if (
    value === "long_term_only" ||
    value === "core_plus_tactical" ||
    value === "tactical_only"
  ) {
    return value;
  }

  return null;
}

export function isOperatingProfileComplete(
  profile: OperatingProfile | null | undefined,
): boolean {
  return Boolean(
    profile?.investmentStyle &&
      profile.intradayAcknowledgedAt &&
      profile.intradayAcknowledgedAt.length > 0,
  );
}
