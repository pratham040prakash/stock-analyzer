/** T4-4 — Spouse / partner review invite (plan sharing, not leaderboard referral). */

export const SPOUSE_REVIEW_INVITE_COPY = {
  panelTitle: "Share your weekly review",
  panelBody:
    "Send a calm, read-only summary to your spouse or partner so they understand the plan — not daily tips or performance bragging.",
  partnerLabel: "Partner",
  copyButton: "Copy invite message",
  copySuccess: "Invite message copied — paste into WhatsApp or email.",
  emailButton: "Draft email",
  emailHint: "Opens your mail app with a pre-filled summary. No referral codes or leaderboard.",
  settingsTitle: "Partner review invite",
  settingsBody:
    "Share your weekly discipline summary with someone you trust. Process and plan — not stock picks.",
  shareIntro:
    "I'm using APEX to stay disciplined with our investing plan. Here's my weekly review summary:",
  shareClosing:
    "This is about our process and plan — not stock tips. Most days, waiting is the win.",
  mailSubject: "Our APEX weekly investing review",
  antiLeaderboard:
    "No referral points, no leaderboard — just a shared view of discipline and the plan.",
} as const;

export function runSpouseReviewInviteCopySelfCheck(): void {
  if (
    !SPOUSE_REVIEW_INVITE_COPY.panelTitle ||
    !SPOUSE_REVIEW_INVITE_COPY.copyButton ||
    !SPOUSE_REVIEW_INVITE_COPY.shareIntro
  ) {
    throw new Error("Spouse review invite copy self-check failed: missing labels");
  }

  if (!SPOUSE_REVIEW_INVITE_COPY.antiLeaderboard.includes("No referral")) {
    throw new Error("Spouse review invite copy self-check failed: anti-leaderboard line");
  }
}
