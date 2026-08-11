import type { Portfolio } from "@/types/portfolio";

/** Logged-in users should never hydrate from demo holdings. */
export const EMPTY_PORTFOLIO: Portfolio = { holdings: [] };
