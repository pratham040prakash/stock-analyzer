import { redirect } from "next/navigation";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";

export default async function JournalPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
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

  const params = await searchParams;
  const query = new URLSearchParams({ tab: "receipts" });

  const receipt = params.receipt;

  if (typeof receipt === "string" && receipt.trim()) {
    query.set("receipt", receipt.trim());
  }

  redirect(`/app/review?${query.toString()}`);
}
