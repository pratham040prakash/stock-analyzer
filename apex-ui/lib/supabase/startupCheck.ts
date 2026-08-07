import { devLog } from "@/lib/env";

/** Dev-only startup diagnostics for Supabase env loading. */
export function logSupabaseEnvCheck(): void {
  if (process.env.NODE_ENV === "production") return;

  devLog("ENV CHECK:", {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL ?? "missing",
    key: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? "loaded" : "missing",
    appUrl: process.env.NEXT_PUBLIC_APP_URL ?? "missing",
  });
}
