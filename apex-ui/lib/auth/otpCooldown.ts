export const OTP_COOLDOWN_SECONDS = 60;
export const OTP_LAST_SENT_KEY = "otp_last_sent";

export function getOtpCooldownRemaining(): number {
  if (typeof window === "undefined") return 0;

  const raw = localStorage.getItem(OTP_LAST_SENT_KEY);
  if (!raw) return 0;

  const sentAt = Number(raw);
  if (!Number.isFinite(sentAt)) return 0;

  const elapsedMs = Date.now() - sentAt;
  const remainingSeconds = Math.ceil(
    (OTP_COOLDOWN_SECONDS * 1000 - elapsedMs) / 1000,
  );

  return remainingSeconds > 0 ? remainingSeconds : 0;
}

export function markOtpSent(): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(OTP_LAST_SENT_KEY, String(Date.now()));
}

export function clearOtpSentMark(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(OTP_LAST_SENT_KEY);
}
