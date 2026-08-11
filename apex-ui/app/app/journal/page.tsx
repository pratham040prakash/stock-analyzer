import { Suspense } from "react";
import { redirect } from "next/navigation";
import JournalPageClient from "@/components/JournalPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";

export default async function JournalPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/journal");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/journal");
  }

  const userName =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    user.email?.split("@")[0] ??
    "there";

  return (
    <Suspense fallback={<p className="p-6 text-sm text-apex-muted">Loading journal…</p>}>
      <JournalPageClient userName={userName} />
    </Suspense>
  );
}
