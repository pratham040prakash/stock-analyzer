import { redirect } from "next/navigation";
import ExplorePageClient from "@/components/explore/ExplorePageClient";
import { createClient } from "@/lib/supabase/server";

export default async function ExplorePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/explore");
  }

  const userName =
    user.user_metadata?.full_name?.split(" ")?.[0] ??
    user.email?.split("@")?.[0] ??
    "Investor";

  return <ExplorePageClient userName={userName} />;
}
