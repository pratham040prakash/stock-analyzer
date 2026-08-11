import { Suspense } from "react";
import { redirect } from "next/navigation";
import ReviewPageClient from "@/components/ReviewPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";

export default async function ReviewPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/review");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/review");
  }

  const userName =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    user.email?.split("@")[0] ??
    "there";

  return (
    <Suspense fallback={<p className="p-6 text-sm text-apex-muted">Loading review…</p>}>
      <ReviewPageClient userName={userName} />
    </Suspense>
  );
}
