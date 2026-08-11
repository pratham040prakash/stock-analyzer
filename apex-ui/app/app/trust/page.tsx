import TrustPageClient from "@/components/you/TrustPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function TrustPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/trust");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/trust");
  }

  return <TrustPageClient />;
}
