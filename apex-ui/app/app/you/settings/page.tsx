import { redirect } from "next/navigation";
import SettingsPageClient from "@/components/you/SettingsPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";

export default async function YouSettingsPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/you/settings");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/you/settings");
  }

  const userName =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    user.email?.split("@")[0] ??
    "there";

  return <SettingsPageClient userName={userName} />;
}
