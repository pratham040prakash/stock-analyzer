import { NextResponse } from "next/server";

export function apiError(message: string, status = 500) {
  return NextResponse.json({ status: "error", message }, { status });
}

export function apiOk<T extends Record<string, unknown>>(data: T, status = 200) {
  const response = NextResponse.json({ status: "ok", ...data }, { status });
  response.headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
  response.headers.set("Pragma", "no-cache");
  return response;
}
