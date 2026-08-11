import ResearchPageClient from "@/components/ResearchPageClient";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function ResearchPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/research");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/research");
  }

  const params = await searchParams;
  const symbol =
    typeof params.symbol === "string" ? params.symbol.trim().toUpperCase() : "";

  return <ResearchPageClient initialSymbol={symbol || null} />;
}
