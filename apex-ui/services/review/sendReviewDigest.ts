import type { ReviewDigestPayload } from "@/services/review/reviewDigest";

export type DigestSendResult = {
  sent: boolean;
  channel: ReviewDigestPayload["channel"];
  detail: string;
};

async function postWebhook(url: string, payload: ReviewDigestPayload): Promise<DigestSendResult> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      subject: payload.subject,
      body: payload.body,
      channel: payload.channel,
    }),
  });

  if (!response.ok) {
    return {
      sent: false,
      channel: payload.channel,
      detail: `Webhook failed (${response.status})`,
    };
  }

  return {
    sent: true,
    channel: payload.channel,
    detail: "Delivered via webhook",
  };
}

async function sendTelegram(payload: ReviewDigestPayload): Promise<DigestSendResult> {
  const token = process.env.TELEGRAM_BOT_TOKEN?.trim();
  const chatId = process.env.TELEGRAM_CHAT_ID?.trim();

  if (!token || !chatId) {
    return {
      sent: false,
      channel: "telegram",
      detail: "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured",
    };
  }

  const text = `${payload.subject}\n\n${payload.body}`.slice(0, 4000);
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text }),
  });

  if (!response.ok) {
    return {
      sent: false,
      channel: "telegram",
      detail: `Telegram API failed (${response.status})`,
    };
  }

  return {
    sent: true,
    channel: "telegram",
    detail: "Delivered via Telegram",
  };
}

export async function sendReviewDigest(
  payload: ReviewDigestPayload,
): Promise<DigestSendResult> {
  if (!payload.enabled || payload.channel === "none") {
    return {
      sent: false,
      channel: "none",
      detail: "Digest disabled (set APEX_REVIEW_DIGEST_ENABLED=true)",
    };
  }

  const webhook = process.env.APEX_DIGEST_WEBHOOK_URL?.trim();

  if (webhook) {
    return postWebhook(webhook, payload);
  }

  if (payload.channel === "telegram") {
    return sendTelegram(payload);
  }

  if (payload.channel === "email") {
    return {
      sent: false,
      channel: "email",
      detail: "Email channel requires APEX_DIGEST_WEBHOOK_URL (email provider)",
    };
  }

  return {
    sent: false,
    channel: payload.channel,
    detail: "No delivery channel configured",
  };
}

export function runSendReviewDigestSelfCheck(): void {
  if (typeof sendReviewDigest !== "function") {
    throw new Error("Send review digest self-check failed");
  }
}
