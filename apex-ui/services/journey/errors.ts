export function resolveInvestmentJourneyDbError(error: unknown): {
  status: number;
  message: string;
} {
  const text =
    error instanceof Error
      ? error.message
      : typeof error === "object" &&
          error &&
          "message" in error &&
          typeof (error as { message: unknown }).message === "string"
        ? (error as { message: string }).message
        : "";

  if (
    text.includes("investment_journeys") &&
    (text.includes("does not exist") || text.includes("schema cache"))
  ) {
    return {
      status: 503,
      message:
        "Journey storage is not ready yet (investment_journeys migration pending). Path saved on this device for now.",
    };
  }

  return {
    status: 500,
    message: "Could not save investment journey.",
  };
}

export function runInvestmentJourneyErrorsSelfCheck(): void {
  const resolved = resolveInvestmentJourneyDbError(
    new Error('relation "public.investment_journeys" does not exist'),
  );

  if (resolved.status !== 503 || !resolved.message.includes("migration pending")) {
    throw new Error("Investment journey errors self-check failed");
  }
}
