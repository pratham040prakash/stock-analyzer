import HowApexWorksClient from "@/components/you/HowApexWorksClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function HowApexWorksPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/you/how-it-works");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/you/how-it-works");
  }

  return <HowApexWorksClient />;
}
