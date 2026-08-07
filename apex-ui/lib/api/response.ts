import { NextResponse } from "next/server";

function jsonResponse(body: Record<string, unknown>, status: number) {
  const response = NextResponse.json(body, { status });
  response.headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Content-Type", "application/json");
  return response;
}

export function apiError(message: string, status = 500) {
  return jsonResponse({ status: "error", message }, status);
}

export function apiOk<T extends Record<string, unknown>>(data: T, status = 200) {
  return jsonResponse({ status: "ok", ...data }, status);
}
