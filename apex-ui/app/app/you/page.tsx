import YouPageClient from "@/components/you/YouPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function YouPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/you");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/you");
  }

  const userName =
    user.user_metadata?.full_name ??
    user.user_metadata?.name ??
    user.email?.split("@")[0] ??
    "Investor";

  return <YouPageClient userName={userName} />;
}
