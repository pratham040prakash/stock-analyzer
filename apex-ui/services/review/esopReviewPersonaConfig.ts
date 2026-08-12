/** ESOP review persona is on by default; set APEX_ESOP_REVIEW_PERSONA_ENABLED=false to hide. */

export function isEsopReviewPersonaEnabled(): boolean {
  return process.env.APEX_ESOP_REVIEW_PERSONA_ENABLED !== "false";
}

export function runEsopReviewPersonaConfigSelfCheck(): void {
  if (typeof isEsopReviewPersonaEnabled() !== "boolean") {
    throw new Error("ESOP review persona config self-check failed: enabled flag");
  }
}
