/**
 * VERIFY-001 — production smoke checks after deploy.
 * VERIFY-002 — authenticated API checks when APEX_VERIFY_COOKIE is set.
 * VERIFY-003 — Today Open P&L contract (positions_pnl + breakdown sum).
 *
 * Usage:
 *   APEX_VERIFY_BASE_URL=https://your-app.vercel.app npm run verify:prod
 *   npm run verify:prod -- https://your-app.vercel.app
 *
 * Use the site root only — not /app or other paths.
 * Optional authenticated checks (browser session cookie):
 *   APEX_VERIFY_COOKIE="sb-..." npm run verify:prod
 */

type CheckResult = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  critical: boolean;
};

type VerifyReport = {
  baseUrl: string;
  checkedAt: string;
  passed: number;
  failed: number;
  checks: CheckResult[];
};

function normalizeBaseUrl(value: string): string {
  let parsed: URL;

  try {
    parsed = new URL(value);
  } catch {
    throw new Error(`Invalid base URL: ${value}`);
  }

  if (parsed.pathname !== "/" && parsed.pathname !== "") {
    console.warn(
      `Ignoring path "${parsed.pathname}" — use the site root (e.g. ${parsed.origin}), not /app.`,
    );
  }

  return parsed.origin;
}

function resolveBaseUrl(): string {
  const fromArg = process.argv.find((arg) => arg.startsWith("http"));

  if (fromArg) {
    return normalizeBaseUrl(fromArg);
  }

  const fromEnv = process.env.APEX_VERIFY_BASE_URL?.trim();

  if (fromEnv) {
    return normalizeBaseUrl(fromEnv);
  }

  throw new Error(
    "Set APEX_VERIFY_BASE_URL or pass the production URL as the first argument (site root only, no /app).",
  );
}

async function fetchCheck(
  url: string,
  options: RequestInit = {},
): Promise<{ status: number; body: unknown; headers: Headers }> {
  const response = await fetch(url, {
    ...options,
    redirect: "manual",
    headers: {
      Accept: "application/json, text/html",
      ...(options.headers ?? {}),
    },
  });

  const contentType = response.headers.get("content-type") ?? "";

  let body: unknown = null;

  if (contentType.includes("application/json")) {
    body = await response.json().catch(() => null);
  } else {
    body = await response.text().catch(() => null);
  }

  return { status: response.status, body, headers: response.headers };
}

function record(
  checks: CheckResult[],
  input: Omit<CheckResult, "ok"> & { ok: boolean },
): void {
  checks.push(input);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function runChecks(baseUrl: string): Promise<VerifyReport> {
  const checks: CheckResult[] = [];
  const cookie = process.env.APEX_VERIFY_COOKIE?.trim();
  const authHeaders = cookie ? { Cookie: cookie } : undefined;

  const health = await fetchCheck(`${baseUrl}/api/health`);
  const healthBody = isRecord(health.body) ? health.body : null;

  record(checks, {
    id: "health-status",
    label: "Health endpoint returns 200",
    ok: health.status === 200,
    detail: `status=${health.status}`,
    critical: true,
  });

  record(checks, {
    id: "health-supabase",
    label: "Supabase connected in health report",
    ok: healthBody?.supabase === "connected",
    detail: String(healthBody?.supabase ?? "missing"),
    critical: true,
  });

  record(checks, {
    id: "health-env",
    label: "Required env configured in health report",
    ok: healthBody?.env === "ok",
    detail: String(healthBody?.env ?? "missing"),
    critical: true,
  });

  record(checks, {
    id: "health-kite-proxy",
    label: "Kite order proxy status exposed in health report",
    ok:
      healthBody?.kite_proxy === "configured" ||
      healthBody?.kite_proxy === "missing",
    detail: String(healthBody?.kite_proxy ?? "missing"),
    critical: false,
  });

  const proxyUrl = process.env.KITE_ORDER_PROXY_URL?.trim();
  if (proxyUrl) {
    try {
      const proxyHealth = await fetchCheck(`${proxyUrl.replace(/\/$/, "")}/egress`);
      const proxyBody = isRecord(proxyHealth.body) ? proxyHealth.body : null;
      record(checks, {
        id: "kite-proxy-egress",
        label: "Kite order proxy egress endpoint reachable",
        ok:
          proxyHealth.status === 200 &&
          typeof proxyBody?.egress_ipv4 === "string" &&
          proxyBody.egress_ipv4.length > 0,
        detail: `status=${proxyHealth.status} ip=${String(proxyBody?.egress_ipv4 ?? "missing")}`,
        critical: false,
      });
    } catch (error) {
      record(checks, {
        id: "kite-proxy-egress",
        label: "Kite order proxy egress endpoint reachable",
        ok: false,
        detail: error instanceof Error ? error.message : "fetch failed",
        critical: false,
      });
    }
  }

  const cacheControl = health.headers.get("cache-control") ?? "";
  record(checks, {
    id: "health-no-store",
    label: "Health response avoids long-lived cache",
    ok:
      cacheControl.includes("no-store") ||
      cacheControl.includes("must-revalidate"),
    detail: cacheControl || "missing",
    critical: false,
  });

  const protectedRoutes = [
    { path: "/api/decision/today", id: "auth-today" },
    { path: "/api/today/brief", id: "auth-brief" },
    { path: "/api/portfolio/overview", id: "auth-portfolio-overview" },
    { path: "/api/receipts", id: "auth-receipts" },
    { path: "/api/discipline/streak", id: "auth-discipline" },
    { path: "/api/trust/outcome", id: "auth-trust" },
    { path: "/api/subscription/tier", id: "auth-tier" },
    { path: "/api/decision/history?days=7", id: "auth-history" },
    { path: "/api/trade/status?stock=RELIANCE", id: "auth-trade-status" },
  ] as const;

  for (const route of protectedRoutes) {
    const result = await fetchCheck(`${baseUrl}${route.path}`);
    const body = isRecord(result.body) ? result.body : null;

    record(checks, {
      id: route.id,
      label: `${route.path} rejects unauthenticated requests`,
      ok: result.status === 401 && body?.status === "error",
      detail:
        result.status === 307
          ? `status=${result.status} (redirect — check base URL is site root, not /app)`
          : `status=${result.status}`,
      critical: true,
    });
  }

  const tradeExecute = await fetchCheck(`${baseUrl}/api/trade/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ side: "sell", stock: "RELIANCE", sellPercent: 25 }),
  });
  const tradeExecuteBody = isRecord(tradeExecute.body) ? tradeExecute.body : null;

  record(checks, {
    id: "auth-trade-execute",
    label: "POST /api/trade/execute rejects unauthenticated requests",
    ok: tradeExecute.status === 401 && tradeExecuteBody?.status === "error",
    detail: `status=${tradeExecute.status}`,
    critical: true,
  });

  const funds = await fetchCheck(`${baseUrl}/api/funds`);
  const fundsBody = isRecord(funds.body) ? funds.body : null;

  record(checks, {
    id: "auth-funds",
    label: "/api/funds rejects unauthenticated session",
    ok:
      funds.status === 200 &&
      fundsBody?.status === "NOT_CONNECTED" &&
      fundsBody?.statusCode === 401,
    detail: `status=${funds.status} body=${String(fundsBody?.status ?? "missing")}`,
    critical: true,
  });

  const login = await fetchCheck(`${baseUrl}/login`);
  record(checks, {
    id: "login-page",
    label: "Login page is reachable",
    ok: login.status === 200,
    detail: `status=${login.status}`,
    critical: true,
  });

  const app = await fetchCheck(`${baseUrl}/app`);
  record(checks, {
    id: "app-guard",
    label: "App route redirects anonymous users to login",
    ok: app.status >= 300 && app.status < 400,
    detail: `status=${app.status}`,
    critical: true,
  });

  if (authHeaders) {
    const authedRoutes = [
      {
        id: "authed-today",
        path: "/api/decision/today",
        validate: (body: Record<string, unknown> | null) =>
          isRecord(body?.decision) && typeof body?.action === "string",
      },
      {
        id: "authed-discipline",
        path: "/api/discipline/streak",
        validate: (body: Record<string, unknown> | null) =>
          body?.status === "ok" && isRecord(body.streak),
      },
      {
        id: "authed-trust",
        path: "/api/trust/outcome",
        validate: (body: Record<string, unknown> | null) =>
          body?.status === "ok" && isRecord(body.trust),
      },
      {
        id: "authed-history",
        path: "/api/decision/history?days=7",
        validate: (body: Record<string, unknown> | null) =>
          body?.status === "ok" && Array.isArray(body.history),
      },
      {
        id: "authed-tier",
        path: "/api/subscription/tier",
        validate: (body: Record<string, unknown> | null) =>
          body?.status === "ok" &&
          (body.tier === "free" || body.tier === "premium"),
      },
      {
        id: "authed-trade-status",
        path: "/api/trade/status?stock=RELIANCE",
        validate: (body: Record<string, unknown> | null) => {
          if (body?.status !== "ok" || typeof body.filledToday !== "boolean") {
            return false;
          }

          if (typeof body.stock !== "string" || body.stock.length === 0) {
            return false;
          }

          if (body.filledToday !== true) {
            return true;
          }

          return (
            (body.orderId === undefined || typeof body.orderId === "string") &&
            (body.quantity === undefined || typeof body.quantity === "number") &&
            (body.side === undefined ||
              body.side === "buy" ||
              body.side === "sell")
          );
        },
      },
      {
        id: "authed-trade-status-jiofin",
        path: "/api/trade/status?stock=JIOFIN",
        validate: (body: Record<string, unknown> | null) =>
          body?.status === "ok" &&
          body.stock === "JIOFIN" &&
          typeof body.filledToday === "boolean",
      },
      {
        id: "authed-funds",
        path: "/api/funds",
        validate: (body: Record<string, unknown> | null) => {
          if (typeof body?.status !== "string") {
            return false;
          }

          if (body.status === "TOKEN_EXPIRED") {
            return body.portfolio_value === null || body.portfolio_value === undefined;
          }

          return (
            typeof body.portfolio_value === "number" &&
            typeof body.margin_available === "number"
          );
        },
      },
      {
        id: "authed-portfolio",
        path: "/api/portfolio",
        validate: (body: Record<string, unknown> | null) => {
          if (typeof body?.status !== "string" || !Array.isArray(body.holdings)) {
            return false;
          }

          if (body.status === "TOKEN_EXPIRED") {
            return body.stale === true || body.holdings.length === 0;
          }

          if (body.status !== "OK") {
            return true;
          }

          const dayPnl = body.day_pnl;
          const positionsPnl = body.positions_pnl;
          const portfolioDayPnl = body.portfolio_day_pnl;

          if (
            typeof dayPnl === "number" &&
            typeof portfolioDayPnl === "number" &&
            Math.abs(dayPnl - portfolioDayPnl) >= 0.01
          ) {
            return false;
          }

          if (
            typeof dayPnl === "number" &&
            typeof positionsPnl === "number" &&
            (Math.abs(dayPnl) > 0.01 || Math.abs(positionsPnl) > 0.01) &&
            Math.abs(dayPnl - positionsPnl) <= 0.01
          ) {
            return false;
          }

          return true;
        },
      },
      {
        id: "authed-today-pnl",
        path: "/api/today/pnl",
        validate: (body: Record<string, unknown> | null) => {
          if (typeof body?.positions_pnl !== "number") {
            return false;
          }

          if (!Array.isArray(body.positions_breakdown)) {
            return false;
          }

          let breakdownSum = 0;
          for (const row of body.positions_breakdown) {
            if (!isRecord(row) || typeof row.pnl !== "number") {
              return false;
            }
            breakdownSum += row.pnl;
          }

          return Math.abs(breakdownSum - body.positions_pnl) < 0.2;
        },
      },
    ] as const;

    for (const route of authedRoutes) {
      const result = await fetchCheck(`${baseUrl}${route.path}`, {
        headers: authHeaders,
      });
      const body = isRecord(result.body) ? result.body : null;

      record(checks, {
        id: route.id,
        label: `${route.path} works with session cookie`,
        ok: result.status === 200 && route.validate(body),
        detail: `status=${result.status}`,
        critical: false,
      });
    }
  } else {
    record(checks, {
      id: "authed-skipped",
      label: "Authenticated API checks skipped",
      ok: true,
      detail: "Set APEX_VERIFY_COOKIE to run session checks",
      critical: false,
    });
  }

  const passed = checks.filter((check) => check.ok).length;
  const failed = checks.filter((check) => !check.ok).length;

  return {
    baseUrl,
    checkedAt: new Date().toISOString(),
    passed,
    failed,
    checks,
  };
}

function printReport(report: VerifyReport): void {
  console.log(`\nAPEX prod verify — ${report.baseUrl}`);
  console.log(`Checked at ${report.checkedAt}\n`);

  for (const check of report.checks) {
    const mark = check.ok ? "PASS" : "FAIL";
    const severity = check.critical ? "critical" : "optional";
    console.log(`[${mark}] ${check.label} (${severity})`);
    console.log(`       ${check.detail}`);
  }

  console.log(
    `\nSummary: ${report.passed} passed · ${report.failed} failed · ${report.checks.length} checks`,
  );
}

async function main(): Promise<void> {
  const baseUrl = resolveBaseUrl();
  const report = await runChecks(baseUrl);

  printReport(report);

  const criticalFailures = report.checks.filter(
    (check) => check.critical && !check.ok,
  );

  if (criticalFailures.length > 0) {
    process.exitCode = 1;
  }
}

void main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
