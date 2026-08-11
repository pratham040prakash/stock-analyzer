import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { exportInvestmentBookMarkdown } from "@/services/thesis/exportInvestmentBook";
import { listInvestmentTheses } from "@/services/thesis/thesisRepository";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const theses = await listInvestmentTheses(supabase, user.id);
  const markdown = exportInvestmentBookMarkdown(theses);

  return new NextResponse(markdown, {
    status: 200,
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": 'attachment; filename="apex-investment-book.md"',
      "Cache-Control": "no-store",
    },
  });
}
