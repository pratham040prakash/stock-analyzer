import type { Metadata } from "next";
import { redirect } from "next/navigation";
import LandingPage from "@/components/landing/LandingPage";
import { createClient } from "@/lib/supabase/server";
import { isSystemConfigured } from "@/lib/env/config";

export const metadata: Metadata = {
  title: "APEX — Your Investment Mentor",
  description:
    "Stop guessing your investments. APEX tells you when to buy, when to wait, and when to stay out — with discipline.",
};

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const requestToken = params.request_token;

  if (typeof requestToken === "string" && requestToken.trim()) {
    const qs = new URLSearchParams();
    qs.set("request_token", requestToken.trim());
    const status = params.status;
    if (typeof status === "string") {
      qs.set("status", status);
    }
    redirect(`/api/zerodha/callback?${qs.toString()}`);
  }

  if (isSystemConfigured()) {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user) {
      redirect("/app");
    }
  }

  return <LandingPage />;
}
