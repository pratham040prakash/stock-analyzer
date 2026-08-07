export function mapAuthErrorMessage(error: { message?: string } | null): string {
  const message = error?.message ?? "";

  if (!message) {
    return "Unable to sign in. Try again.";
  }

  const lower = message.toLowerCase();

  if (
    lower.includes("valid email") ||
    lower.includes("invalid email") ||
    lower.includes("email address")
  ) {
    return "Enter a valid email";
  }

  if (lower.includes("invalid login")) {
    return "Invalid email or login issue";
  }

  if (lower.includes("rate limit")) {
    return "You're already set — your login link is on the way. Give it a moment.";
  }

  if (
    isNetworkErrorMessage(message) ||
    (typeof navigator !== "undefined" && !navigator.onLine)
  ) {
    return "Check your connection";
  }

  return message;
}

export function isRateLimitError(message: string): boolean {
  return message.toLowerCase().includes("rate limit");
}

export function isNetworkErrorMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("network") ||
    lower.includes("fetch") ||
    lower.includes("connection") ||
    lower.includes("timeout")
  );
}
