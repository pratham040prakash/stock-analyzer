import { sendImmediateAlert } from "@/services/review/sendReviewDigest";

export async function sendDeskAlert(input: {
  title: string;
  body: string;
}): Promise<boolean> {
  const result = await sendImmediateAlert({
    subject: input.title,
    body: input.body,
  });
  return result.sent;
}

export function runDeskInterruptSelfCheck(): void {
  if (typeof sendDeskAlert !== "function") {
    throw new Error("Desk interrupt self-check failed");
  }
}
