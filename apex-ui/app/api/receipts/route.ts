import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  dismissDecisionReceipt,
  listDecisionReceipts,
  persistDecisionReceipt,
  type PersistReceiptInput,
} from "@/services/receipts/persistReceipt";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const days = Number(searchParams.get("days") ?? "30");

  const receipts = await listDecisionReceipts(supabase, user.id, days);

  return NextResponse.json({ status: "ok", receipts });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: PersistReceiptInput;

  try {
    body = (await request.json()) as PersistReceiptInput;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (!body.symbol?.trim()) {
    return apiError("symbol is required", 400);
  }

  const receipt = await persistDecisionReceipt(supabase, user.id, body);

  if (!receipt) {
    return apiError("Could not persist receipt", 500);
  }

  return NextResponse.json({ status: "ok", receipt });
}

export async function PATCH(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: { id?: string };

  try {
    body = (await request.json()) as { id?: string };
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  if (!body.id) {
    return apiError("id is required", 400);
  }

  const ok = await dismissDecisionReceipt(supabase, user.id, body.id);

  if (!ok) {
    return apiError("Could not dismiss receipt", 500);
  }

  return NextResponse.json({ status: "ok" });
}
