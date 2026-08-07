import { devError, devLog } from "@/lib/env";

const PLACEHOLDER_MARKERS = [
  "your-project",
  "YOUR_PROJECT",
  "your_supabase_anon_key",
  "YOUR_PUBLIC_ANON_KEY",
];

function isPlaceholderValue(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return PLACEHOLDER_MARKERS.some((marker) =>
    normalized.includes(marker.toLowerCase()),
  );
}

export function validateSupabaseEnv(): boolean {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !key || isPlaceholderValue(url) || isPlaceholderValue(key)) {
    devError("[APEX Auth] Supabase ENV missing", {
      hasUrl: Boolean(url),
      hasKey: Boolean(key),
      urlPlaceholder: url ? isPlaceholderValue(url) : false,
      keyPlaceholder: key ? isPlaceholderValue(key) : false,
    });
    return false;
  }

  devLog("[APEX Auth] Supabase client configured", { url });

  return true;
}

export function isSupabaseConfigured(): boolean {
  return validateSupabaseEnv();
}
