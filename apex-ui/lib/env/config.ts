import { isTokenEncryptionConfigured } from "@/lib/crypto/encrypt";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import { isSupabaseConfigured } from "@/lib/supabase/env";

export const SYSTEM_CONFIG_INCOMPLETE_MESSAGE =
  "System configuration incomplete";

const PLACEHOLDER_MARKERS = [
  "your-app.vercel.app",
  "your-project",
  "your_api_key",
  "changeme",
];

function isPlaceholderValue(value: string | undefined): boolean {
  if (!value) return true;
  const normalized = value.trim().toLowerCase();
  return PLACEHOLDER_MARKERS.some((marker) => normalized.includes(marker));
}

function isLocalhostUrl(url: string): boolean {
  try {
    const host = new URL(url).hostname;
    return host === "localhost" || host === "127.0.0.1";
  } catch {
    return false;
  }
}

function isProductionDeploy(): boolean {
  return process.env.NODE_ENV === "production" || Boolean(process.env.VERCEL);
}

/** Canonical public app URL for OAuth redirects (Vercel production/preview). */
export function getAppBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_APP_URL?.trim();
  if (configured && !isPlaceholderValue(configured)) {
    if (!isProductionDeploy() || !isLocalhostUrl(configured)) {
      return configured.replace(/\/$/, "");
    }
  }

  const vercelUrl = process.env.VERCEL_URL?.trim();
  if (vercelUrl) {
    return `https://${vercelUrl.replace(/\/$/, "")}`;
  }

  return "";
}

/** Resolve base URL on server with optional request origin fallback. */
export function resolveAppBaseUrl(fallbackOrigin?: string): string {
  const fromEnv = getAppBaseUrl();
  if (fromEnv) return fromEnv;
  if (fallbackOrigin) return fallbackOrigin.replace(/\/$/, "");
  return "";
}

/** Client-safe base URL: env first, then current origin (non-localhost on Vercel). */
export function getClientAppBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_APP_URL?.trim();
  if (configured && !isPlaceholderValue(configured)) {
    if (!isProductionDeploy() || !isLocalhostUrl(configured)) {
      return configured.replace(/\/$/, "");
    }
  }

  if (typeof window !== "undefined") {
    const origin = window.location.origin.replace(/\/$/, "");
    if (!isProductionDeploy() || !isLocalhostUrl(origin)) {
      return origin;
    }
  }

  return getAppBaseUrl();
}

/** Server/client auth callback URL — prefers env, then Vercel URL, then request origin. */
export function resolveAuthCallbackUrl(fallbackOrigin?: string): string {
  const base = resolveAppBaseUrl(fallbackOrigin);
  return base ? `${base}/auth/callback` : "/auth/callback";
}

export function getAuthCallbackUrl(): string {
  return resolveAuthCallbackUrl(
    typeof window !== "undefined" ? window.location.origin : undefined,
  );
}

export function getZerodhaCallbackUrl(fallbackOrigin?: string): string {
  const base = resolveAppBaseUrl(fallbackOrigin);
  return base ? `${base}/api/zerodha/callback` : "/api/zerodha/callback";
}

/** @deprecated Kite Connect redirect must use getZerodhaCallbackUrl in the developer portal. */
export function getZerodhaRedirectUrl(): string {
  return getZerodhaCallbackUrl();
}

export function isAppUrlConfigured(): boolean {
  return Boolean(getAppBaseUrl()) || Boolean(process.env.VERCEL_URL?.trim());
}

export function isSystemConfigured(): boolean {
  return isSupabaseConfigured();
}

export type SystemConfigReport = {
  ok: boolean;
  supabase: boolean;
  appUrl: boolean;
  serviceRole: boolean;
  zerodha: boolean;
  encryption: boolean;
  cron: boolean;
  missing: string[];
};

export function getSystemConfigReport(): SystemConfigReport {
  const supabase = isSupabaseConfigured();
  const appUrl = isAppUrlConfigured();
  const serviceRole = Boolean(process.env.SUPABASE_SERVICE_ROLE_KEY?.trim());
  const zerodha = getZerodhaConfig().configured;
  const encryption = isTokenEncryptionConfigured();
  const cron = Boolean(process.env.CRON_SECRET?.trim());

  const missing: string[] = [];
  if (!supabase) {
    missing.push("NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY");
  }
  if (!appUrl) missing.push("NEXT_PUBLIC_APP_URL");
  if (!serviceRole) missing.push("SUPABASE_SERVICE_ROLE_KEY");
  if (!zerodha) missing.push("ZERODHA_API_KEY", "ZERODHA_API_SECRET");
  if (!encryption) missing.push("TOKEN_ENCRYPTION_KEY");
  if (!cron) missing.push("CRON_SECRET");

  return {
    ok: supabase && appUrl && serviceRole,
    supabase,
    appUrl,
    serviceRole,
    zerodha,
    encryption,
    cron,
    missing,
  };
}
