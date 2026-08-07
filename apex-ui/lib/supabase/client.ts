import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "@/types/database";
import { validateSupabaseEnv } from "@/lib/supabase/env";

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey || !validateSupabaseEnv()) {
    throw new Error("Supabase ENV not configured");
  }

  return createBrowserClient<Database>(supabaseUrl, supabaseKey);
}

export { isSupabaseConfigured } from "@/lib/supabase/env";
