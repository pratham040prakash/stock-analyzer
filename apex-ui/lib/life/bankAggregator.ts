import {
  reviewStatement,
  type StatementRow,
} from "@/lib/life/financialFreedom";

export type BankConsentStatus =
  | "off"
  | "pending"
  | "active"
  | "fetched"
  | "failed"
  | "rejected";

export type BankMonthReview = {
  salaryInr: number;
  needsInr: number;
  leaksInr: number;
  emiInr: number;
  rowCount: number;
};

export function normalizeIndianMobile(raw: string): string | null {
  const digits = raw.replace(/\D/g, "");
  const ten =
    digits.length === 12 && digits.startsWith("91") ? digits.slice(2) : digits;
  return /^[6-9]\d{9}$/.test(ten) ? ten : null;
}

export function mobileLast4(mobile: string): string {
  return mobile.slice(-4);
}

export function sixMonthDataRange(now = new Date()): { from: string; to: string } {
  const to = new Date(now);
  const from = new Date(now);
  from.setUTCMonth(from.getUTCMonth() - 6);
  return { from: from.toISOString(), to: to.toISOString() };
}

export function buildConsentBody(mobile: string, now = new Date()) {
  const range = sixMonthDataRange(now);
  return {
    consentDuration: { unit: "MONTH", value: "6" },
    vua: mobile,
    dataRange: range,
    fiTypes: ["DEPOSIT"],
    consentTypes: ["TRANSACTIONS", "SUMMARY"],
    additionalParams: {
      purposeCode: "102",
      purposeDescription: "Personal spending plan. Only leftover may invest.",
      tags: ["APEX_LIFE"],
    },
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function asList(value: unknown): unknown[] {
  if (value == null) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function readAmount(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.abs(value);
  }
  if (typeof value === "string") {
    const parsed = Number(value.replace(/[^0-9.-]/g, ""));
    return Number.isFinite(parsed) ? Math.abs(parsed) : 0;
  }
  return 0;
}

function isCredit(type: unknown): boolean {
  return /^(CR|CREDIT)$/i.test(String(type ?? "").trim());
}

function transactionToRow(value: unknown): StatementRow | null {
  const row = asRecord(value);
  if (!row) {
    return null;
  }

  const description = String(row.narration ?? row.description ?? row.remark ?? "").trim();
  const amountInr = readAmount(row.amount ?? row.transactionAmount);
  if (!description || amountInr <= 0) {
    return null;
  }

  return {
    description,
    amountInr,
    credit: isCredit(row.type ?? row.txnType),
  };
}

function collectFromAccount(account: unknown, into: StatementRow[]): void {
  const node = asRecord(account);
  if (!node) {
    return;
  }

  const transactions = asRecord(node.transactions);
  const list = asList(transactions?.transaction ?? node.transaction);
  for (const item of list) {
    const row = transactionToRow(item);
    if (row) {
      into.push(row);
    }
  }
}

export function extractBankTransactions(payload: unknown): StatementRow[] {
  const rows: StatementRow[] = [];
  const root = asRecord(payload);
  if (!root) {
    return rows;
  }

  for (const block of asList(root.fiData ?? root.payload)) {
    const fi = asRecord(block);
    for (const item of asList(fi?.data)) {
      const entry = asRecord(item);
      collectFromAccount(asRecord(entry?.decryptedFI)?.account ?? entry?.decryptedFI, rows);
    }
  }

  for (const fip of asList(root.fips)) {
    const node = asRecord(fip);
    for (const account of asList(node?.accounts)) {
      const entry = asRecord(account);
      const data = asRecord(entry?.data);
      collectFromAccount(data?.account ?? data, rows);
    }
  }

  return rows.slice(0, 1_500);
}

export function reviewBankPayload(payload: unknown): BankMonthReview {
  const rows = extractBankTransactions(payload);
  return {
    ...reviewStatement(rows),
    rowCount: rows.length,
  };
}

export function rowsFromBankReview(review: BankMonthReview): StatementRow[] {
  const rows: StatementRow[] = [];
  if (review.salaryInr > 0) {
    rows.push({ description: "SALARY", amountInr: review.salaryInr, credit: true });
  }
  if (review.needsInr > 0) {
    rows.push({ description: "RENT", amountInr: review.needsInr, credit: false });
  }
  if (review.leaksInr > 0) {
    rows.push({ description: "SWIGGY", amountInr: review.leaksInr, credit: false });
  }
  if (review.emiInr > 0) {
    rows.push({ description: "CARD EMI", amountInr: review.emiInr, credit: false });
  }
  return rows;
}

export function bankConnectHint(configured: boolean): string {
  return configured
    ? "The bank sends the last 6 months after you approve on the next screen."
    : "Bank rail is off until Setu keys sit on the server. Kite cash still loads.";
}

export function bankFetchedNote(rowCount: number): string {
  return `Fetched ${rowCount} lines from your bank. Nothing typed.`;
}

export function readSetuConfig(env: NodeJS.ProcessEnv = process.env): {
  configured: boolean;
  clientId: string;
  clientSecret: string;
  productInstanceId: string;
  fiuBaseUrl: string;
  authUrl: string;
  webhookSecret: string;
} {
  const clientId = env.SETU_CLIENT_ID?.trim() ?? "";
  const clientSecret = env.SETU_CLIENT_SECRET?.trim() ?? "";
  const productInstanceId = env.SETU_PRODUCT_INSTANCE_ID?.trim() ?? "";
  return {
    configured: Boolean(clientId && clientSecret && productInstanceId),
    clientId,
    clientSecret,
    productInstanceId,
    fiuBaseUrl: (env.SETU_FIU_BASE_URL?.trim() || "https://fiu-sandbox.setu.co/v2").replace(
      /\/$/,
      "",
    ),
    authUrl: env.SETU_AUTH_URL?.trim() || "https://uat.setu.co/api/v2/auth/token",
    webhookSecret: env.SETU_WEBHOOK_SECRET?.trim() ?? "",
  };
}

export function webhookSecretMatches(headerSecret: string | null, expected: string): boolean {
  if (!expected) {
    return true;
  }
  const got = (headerSecret ?? "").replace(/^Bearer\s+/i, "").trim();
  return got === expected;
}

export function runBankAggregatorSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Bank aggregator self-check failed: ${message}`);
    }
  };

  assert(normalizeIndianMobile("9876543210") === "9876543210", "Ten-digit mobile must pass");
  assert(normalizeIndianMobile("919876543210") === "9876543210", "91 prefix must strip");
  assert(normalizeIndianMobile("12345") === null, "Short mobile must fail");
  assert(buildConsentBody("9876543210").fiTypes.includes("DEPOSIT"), "Consent is deposit accounts");
  assert(
    !buildConsentBody("9876543210").consentTypes.includes("PROFILE"),
    "Do not ask the bank for PAN profile",
  );

  const review = reviewBankPayload({
    type: "FI_DATA_READY",
    fiData: [
      {
        data: [
          {
            decryptedFI: {
              account: {
                transactions: {
                  transaction: [
                    {
                      amount: "120000",
                      narration: "SALARY SEPTEMBER",
                      type: "CREDIT",
                    },
                    {
                      amount: "420",
                      narration: "SWIGGY BANGALORE",
                      type: "DEBIT",
                    },
                  ],
                },
              },
            },
          },
        ],
      },
    ],
  });
  assert(review.salaryInr === 120_000, "AA salary credit must land");
  assert(review.leaksInr === 420, "AA Swiggy debit must be a leak");
  assert(bankFetchedNote(12).includes("from your bank"), "Fetched copy must name the bank");
  assert(
    readSetuConfig({}).configured === false,
    "Missing Setu keys must not pretend the rail is live",
  );
}
