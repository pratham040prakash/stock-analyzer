import type { Metadata } from "next";
import { redirect } from "next/navigation";
import LandingPage from "@/components/landing/LandingPage";
import { WAIT_DAY_BRAND } from "@/lib/gtm/waitDayBrandCopy";
import { getAppBaseUrl, isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";

const baseUrl = getAppBaseUrl();

export const metadata: Metadata = {
  title: WAIT_DAY_BRAND.pageTitle,
  description: WAIT_DAY_BRAND.metaDescription,
  openGraph: {
    title: WAIT_DAY_BRAND.ogTitle,
    description: WAIT_DAY_BRAND.ogDescription,
    type: "website",
    ...(baseUrl ? { url: baseUrl } : {}),
  },
  twitter: {
    card: "summary_large_image",
    title: WAIT_DAY_BRAND.ogTitle,
    description: WAIT_DAY_BRAND.ogDescription,
  },
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
