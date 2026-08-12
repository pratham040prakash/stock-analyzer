/** Spouse review invite is on by default; set APEX_SPOUSE_REVIEW_INVITE_ENABLED=false to hide. */

export function isSpouseReviewInviteEnabled(): boolean {
  return process.env.APEX_SPOUSE_REVIEW_INVITE_ENABLED !== "false";
}

export function runSpouseReviewInviteConfigSelfCheck(): void {
  if (typeof isSpouseReviewInviteEnabled() !== "boolean") {
    throw new Error("Spouse review invite config self-check failed: enabled flag");
  }
}
