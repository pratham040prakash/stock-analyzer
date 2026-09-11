import { formatInr } from "@/lib/funds";

export type LifeLoan = {
  name: string;
  balanceInr: number;
  emiInr: number;
  aprPct: number;
};

export type SpendBucket = "salary" | "emi" | "need" | "leak" | "transfer" | "other";

export type StatementRow = {
  description: string;
  amountInr: number;
  credit: boolean;
};

export type LifeFreedomPlan = {
  salaryInr: number;
  needsInr: number;
  leaksInr: number;
  emiInr: number;
  leftoverInr: number;
  investInr: number;
  closeLoanFirst: string | null;
  headline: string;
  spendLine: string;
  leftoverLine: string;
};

const STORAGE_KEY = "apex_life_freedom";

export function monthsToCloseLoan(input: {
  balanceInr: number;
  emiInr: number;
  aprPct: number;
}): number | null {
  const balance = Math.max(0, input.balanceInr);
  const emi = Math.max(0, input.emiInr);
  const monthlyRate = Math.max(0, input.aprPct) / 12 / 100;
  if (balance <= 0 || emi <= 0) {
    return null;
  }

  if (monthlyRate === 0) {
    return Math.ceil(balance / emi);
  }

  if (emi <= balance * monthlyRate) {
    return null;
  }

  const months = Math.log(emi / (emi - balance * monthlyRate)) / Math.log(1 + monthlyRate);
  if (!Number.isFinite(months) || months <= 0) {
    return null;
  }

  return Math.ceil(months);
}

export function extraPaymentSavesMonths(input: {
  balanceInr: number;
  emiInr: number;
  aprPct: number;
  extraInr: number;
}): number {
  const base = monthsToCloseLoan(input);
  const faster = monthsToCloseLoan({
    ...input,
    emiInr: input.emiInr + Math.max(0, input.extraInr),
  });
  if (base === null || faster === null || faster >= base) {
    return 0;
  }

  return base - faster;
}

export function pickLoanToClose(loans: LifeLoan[]): LifeLoan | null {
  const open = loans.filter((loan) => loan.balanceInr > 0 && loan.emiInr > 0);
  if (open.length === 0) {
    return null;
  }

  return [...open].sort((left, right) => right.aprPct - left.aprPct)[0] ?? null;
}

export function categorizeNarration(description: string): SpendBucket {
  const text = description.trim().toUpperCase();
  if (!text) {
    return "other";
  }

  if (/\b(SALARY|NEFT CR|SAL CR|PAYROLL|WAGES)\b/.test(text)) {
    return "salary";
  }

  if (/\b(EMI|LOAN|BAJAJ FIN|HDFC BANK LOAN|ICICI LOAN)\b/.test(text)) {
    return "emi";
  }

  if (/\b(RENT|MAINTENANCE|ELECTRIC|BESCOM|BWSSB|GAS|SCHOOL FEE)\b/.test(text)) {
    return "need";
  }

  if (/\b(UPI.*REFUND|IMPS|NEFT DR|TRANSFER|OWN A\/C)\b/.test(text)) {
    return "transfer";
  }

  if (
    /\b(SWIGGY|ZOMATO|AMAZON|FLIPKART|NETFLIX|HOTSTAR|CRED|IRCTC|BOOKMYSHOW|MYNTRA)\b/.test(
      text,
    )
  ) {
    return "leak";
  }

  return "other";
}

export function reviewStatement(rows: StatementRow[]): {
  salaryInr: number;
  needsInr: number;
  leaksInr: number;
  emiInr: number;
} {
  let salaryInr = 0;
  let needsInr = 0;
  let leaksInr = 0;
  let emiInr = 0;

  for (const row of rows) {
    const amount = Math.abs(row.amountInr);
    if (!Number.isFinite(amount) || amount <= 0) {
      continue;
    }

    const bucket = categorizeNarration(row.description);
    if (row.credit && (bucket === "salary" || amount >= 20_000)) {
      salaryInr += amount;
      continue;
    }

    if (row.credit) {
      continue;
    }

    if (bucket === "emi") {
      emiInr += amount;
    } else if (bucket === "need") {
      needsInr += amount;
    } else if (bucket === "leak") {
      leaksInr += amount;
    } else if (bucket !== "transfer") {
      needsInr += amount;
    }
  }

  return { salaryInr, needsInr, leaksInr, emiInr };
}

const STATEMENT_ROW_CAP = 1_500;

function csvNumber(value: string): number {
  const parsed = Number(value.replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function splitDelimited(line: string, delim: string): string[] {
  const cells: string[] = [];
  let current = "";
  let inQuotes = false;
  for (const ch of line) {
    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (ch === delim && !inQuotes) {
      cells.push(current.trim());
      current = "";
      continue;
    }
    current += ch;
  }
  cells.push(current.trim());
  return cells;
}

function looksLikeHeader(cells: string[]): boolean {
  const joined = cells.join(" ").toLowerCase();
  const hasDesc = /narr|desc|particular|remark/.test(joined);
  const hasAmt =
    /withdraw|debit|deposit|amount|cr\s*\/\s*dr|dr\s*\/\s*cr/.test(joined) ||
    cells.some((cell) => /^(dr|cr)$/i.test(cell));
  return hasDesc && hasAmt && cells.length >= 3;
}

function detectDelim(line: string): string {
  const counts: Array<[string, number]> = [
    ["\t", (line.match(/\t/g) ?? []).length],
    [";", (line.match(/;/g) ?? []).length],
    ["|", (line.match(/\|/g) ?? []).length],
    [",", (line.match(/,/g) ?? []).length],
  ];
  counts.sort((left, right) => right[1] - left[1]);
  return counts[0][1] >= 2 ? counts[0][0] : ",";
}

function htmlTableText(text: string): string | null {
  if (!/<table/i.test(text)) {
    return null;
  }

  const rows = [...text.matchAll(/<tr[\s\S]*?<\/tr>/gi)].map((match) => {
    const cells = [...match[0].matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi)].map((cell) =>
      cell[1].replace(/<[^>]+>/g, " ").replace(/&nbsp;/gi, " ").replace(/\s+/g, " ").trim(),
    );
    return cells.join(",");
  });
  return rows.length >= 2 ? rows.join("\n") : null;
}

function headerIndex(header: string[], pattern: RegExp): number {
  return header.findIndex((cell) => pattern.test(cell));
}

function rowsFromTable(text: string): StatementRow[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) {
    return [];
  }

  let headerAt = -1;
  let delim = ",";
  const scan = Math.min(lines.length, 30);
  for (let index = 0; index < scan; index += 1) {
    const candidate = detectDelim(lines[index]);
    const cells = splitDelimited(lines[index], candidate);
    if (looksLikeHeader(cells)) {
      headerAt = index;
      delim = candidate;
      break;
    }
  }
  if (headerAt < 0) {
    return [];
  }

  const header = splitDelimited(lines[headerAt], delim).map((cell) => cell.toLowerCase());
  const descIdx = headerIndex(header, /narr|desc|particular|remark/);
  const typeIdx = headerIndex(header, /cr\s*\/\s*dr|dr\s*\/\s*cr|tran(saction)?\s*type/);
  const debitIdx = header.findIndex(
    (cell) => /withdraw|debit/.test(cell) || /^(dr)$/i.test(cell),
  );
  const creditIdx = header.findIndex(
    (cell) =>
      (/deposit|credit/.test(cell) && !/cr\s*\/\s*dr/.test(cell)) || /^(cr)$/i.test(cell),
  );
  const amountIdx = header.findIndex(
    (cell) => /amount/.test(cell) && !/balance/.test(cell) && cell !== header[debitIdx] && cell !== header[creditIdx],
  );
  const rows: StatementRow[] = [];

  for (const line of lines.slice(headerAt + 1)) {
    const cells = splitDelimited(line, delim);
    const description =
      (descIdx >= 0 ? cells[descIdx] : null) ??
      cells.find((cell, index) => index > 0 && /[A-Za-z]{3,}/.test(cell)) ??
      "";
    let amountInr = 0;
    let credit = false;
    const type = (typeIdx >= 0 ? cells[typeIdx] : "").toUpperCase();

    if (typeIdx >= 0 && amountIdx >= 0 && /^(CR|DR|CREDIT|DEBIT)$/.test(type.trim())) {
      amountInr = Math.abs(csvNumber(cells[amountIdx] ?? ""));
      credit = /CR|CREDIT/.test(type);
    } else if (debitIdx >= 0 || creditIdx >= 0) {
      const debit = debitIdx >= 0 ? csvNumber(cells[debitIdx] ?? "") : 0;
      const deposit = creditIdx >= 0 ? csvNumber(cells[creditIdx] ?? "") : 0;
      if (deposit > 0) {
        amountInr = deposit;
        credit = true;
      } else if (debit > 0) {
        amountInr = debit;
      }
    } else if (amountIdx >= 0) {
      const raw = csvNumber(cells[amountIdx] ?? "");
      amountInr = Math.abs(raw);
      credit = raw > 0;
    }

    if (amountInr <= 0 || !description) {
      continue;
    }

    rows.push({
      description,
      amountInr,
      credit: credit || /salary|neft cr|payroll/i.test(description),
    });
  }

  return rows;
}

export function parseBankCsv(text: string): StatementRow[] {
  const fromHtml = htmlTableText(text);
  return rowsFromTable(fromHtml ?? text).slice(0, STATEMENT_ROW_CAP);
}

export function ingestBankStatements(texts: string[]): StatementRow[] {
  return texts.flatMap((text) => parseBankCsv(text)).slice(0, STATEMENT_ROW_CAP);
}

export function statementIngestHint(): string {
  return "Drop the CSVs your bank already emails or exports. Last 6 months. Stays on this device.";
}

export function statementIngestNote(rowCount: number, fileCount: number): string {
  if (rowCount <= 0) {
    return "Could not read those files. Export CSV or Excel from netbanking — not the locked PDF.";
  }
  const files = fileCount === 1 ? "1 file" : `${fileCount} files`;
  return `Read ${rowCount} lines from ${files}. Nothing uploaded.`;
}

export function autoFetchNote(input: {
  salaryFromProfile?: boolean;
  kiteCashInr?: number | null;
}): string {
  const parts: string[] = [];
  if (input.salaryFromProfile) {
    parts.push("Salary from your profile.");
  }
  if (input.kiteCashInr !== null && input.kiteCashInr !== undefined && input.kiteCashInr > 0) {
    parts.push(`Kite already holds ${formatInr(input.kiteCashInr)}.`);
  }
  parts.push("Bank and loans are not on Zerodha.");
  return parts.join(" ");
}

export function assembleLifeFreedomPlan(input: {
  salaryInr: number;
  loans: LifeLoan[];
  statement?: StatementRow[];
  needsInr?: number | null;
  kiteCashInr?: number | null;
}): LifeFreedomPlan {
  const reviewed = input.statement && input.statement.length > 0
    ? reviewStatement(input.statement)
    : null;
  const salary = Math.max(
    0,
    Math.round(reviewed?.salaryInr && reviewed.salaryInr > 0 ? reviewed.salaryInr : input.salaryInr),
  );
  const target = pickLoanToClose(input.loans);
  const emi = Math.max(
    0,
    Math.round(
      reviewed?.emiInr && reviewed.emiInr > 0
        ? reviewed.emiInr
        : input.loans.reduce((sum, loan) => sum + Math.max(0, loan.emiInr), 0),
    ),
  );
  const needs = Math.max(
    0,
    Math.round(
      reviewed?.needsInr && reviewed.needsInr > 0
        ? reviewed.needsInr
        : input.needsInr && input.needsInr > 0
          ? input.needsInr
          : salary * 0.5,
    ),
  );
  const leaks = Math.max(0, Math.round(reviewed?.leaksInr ?? 0));
  const leftover = Math.max(0, salary - needs - leaks - emi);
  const expensive = target !== null && target.aprPct >= 12;
  const extra = expensive ? leftover : 0;
  const saved = target
    ? extraPaymentSavesMonths({
        balanceInr: target.balanceInr,
        emiInr: target.emiInr,
        aprPct: target.aprPct,
        extraInr: extra,
      })
    : 0;
  const investInr = expensive ? 0 : leftover;
  const closeLoanFirst =
    target && expensive
      ? `Close ${target.name} first (${target.aprPct}% ). Extra ${formatInr(leftover)} cuts about ${saved} months.`
      : target
        ? `${target.name} is cheap enough that leftover may invest after EMI.`
        : null;

  return {
    salaryInr: salary,
    needsInr: needs,
    leaksInr: leaks,
    emiInr: emi,
    leftoverInr: leftover,
    investInr,
    closeLoanFirst,
    headline:
      salary <= 0
        ? "Write this month's salary. Freedom starts from the pay-in."
        : expensive
          ? `This month: pay the life, then kill ${target?.name ?? "the loan"}. Do not shop.`
          : "This month: pay the life, then leftover may reach Today.",
    spendLine:
      leaks > 0
        ? `Spend ${formatInr(needs)} on needs · ${formatInr(leaks)} leaked · EMI ${formatInr(emi)}.`
        : `Spend ${formatInr(needs)} on needs · EMI ${formatInr(emi)}.`,
    leftoverLine:
      investInr > 0
        ? `${formatInr(investInr)} leftover is the only money Today may place.${
            input.kiteCashInr && input.kiteCashInr > 0
              ? ` Kite already holds ${formatInr(input.kiteCashInr)}.`
              : ""
          }`
        : leftover > 0
          ? `${formatInr(leftover)} leftover goes to the loan, not a third name.`
          : "No leftover this month. The plan is the salary, not a stock.",
  };
}

export type StoredLifeFreedom = {
  salaryInr: number;
  loans: LifeLoan[];
};

export function readStoredLifeFreedom(): StoredLifeFreedom {
  if (typeof window === "undefined") {
    return { salaryInr: 0, loans: [] };
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { salaryInr: 0, loans: [] };
    }

    const parsed = JSON.parse(raw) as StoredLifeFreedom;
    return {
      salaryInr: Math.max(0, Math.round(parsed.salaryInr ?? 0)),
      loans: Array.isArray(parsed.loans)
        ? parsed.loans
            .map((loan) => ({
              name: String(loan.name ?? "").trim() || "Loan",
              balanceInr: Math.max(0, Math.round(loan.balanceInr ?? 0)),
              emiInr: Math.max(0, Math.round(loan.emiInr ?? 0)),
              aprPct: Math.max(0, Number(loan.aprPct ?? 0)),
            }))
            .slice(0, 8)
        : [],
    };
  } catch {
    return { salaryInr: 0, loans: [] };
  }
}

export function writeStoredLifeFreedom(next: StoredLifeFreedom): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      salaryInr: Math.max(0, Math.round(next.salaryInr)),
      loans: next.loans.slice(0, 8),
    }),
  );
}

export function runFinancialFreedomSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Financial freedom self-check failed: ${message}`);
    }
  };

  const months = monthsToCloseLoan({
    balanceInr: 120_000,
    emiInr: 12_000,
    aprPct: 18,
  });
  assert(months !== null && months > 0 && months < 20, "An 18% loan must have a close date");

  const saved = extraPaymentSavesMonths({
    balanceInr: 120_000,
    emiInr: 12_000,
    aprPct: 18,
    extraInr: 8_000,
  });
  assert(saved >= 2, "Extra payment must shorten the loan");

  const worst = pickLoanToClose([
    { name: "Home", balanceInr: 2_000_000, emiInr: 20_000, aprPct: 8.5 },
    { name: "Card", balanceInr: 80_000, emiInr: 8_000, aprPct: 36 },
  ]);
  assert(worst?.name === "Card", "Close the expensive loan first");

  assert(categorizeNarration("SWIGGY BANGALORE") === "leak", "Food apps are leaks");
  assert(categorizeNarration("SALARY SEPTEMBER") === "salary", "Salary credit must be seen");
  assert(
    parseBankCsv(
      "Date,Narration,Withdrawal,Deposit\n01-09-2026,SALARY SEPTEMBER,0,120000\n02-09-2026,SWIGGY,420,0",
    ).length === 2,
    "Bank CSV must parse salary and a spend",
  );
  assert(
    parseBankCsv(
      "Account Statement\nHDFC0001\nDate,Narration,Chq/Ref No,Value Dt,Withdrawal Amt,Deposit Amt,Closing Balance\n01/09/26,SALARY SEPTEMBER,,01/09/26,,120000,120000\n02/09/26,SWIGGY BANGALORE,,02/09/26,420,,119580",
    ).length === 2,
    "HDFC export with a preamble must parse",
  );
  assert(
    parseBankCsv(
      "S No.,Transaction ID,Value Date,Txn Posted Date,ChequeNo.,Description,Cr/Dr,Transaction Amount(INR),Available Balance(INR)\n1,A1,01-09-2026,01-09-2026,,SALARY SEPTEMBER,CR,120000,120000\n2,A2,02-09-2026,02-09-2026,,SWIGGY,DR,420,119580",
    ).some((row) => row.description === "SWIGGY" && !row.credit && row.amountInr === 420),
    "ICICI Cr/Dr export must parse a debit",
  );
  assert(
    ingestBankStatements([
      "Date,Narration,Withdrawal,Deposit\n01-08-2026,RENT,25000,0",
      "Date,Narration,Withdrawal,Deposit\n01-09-2026,RENT,25000,0",
    ]).length === 2,
    "Two months must merge",
  );
  assert(
    statementIngestHint().includes("bank already emails"),
    "Ingest must ask for the file the bank already sends",
  );
  assert(
    statementIngestNote(0, 1).includes("locked PDF"),
    "Locked bank PDFs are not the ingest path",
  );

  const plan = assembleLifeFreedomPlan({
    salaryInr: 120_000,
    loans: [{ name: "Card", balanceInr: 80_000, emiInr: 8_000, aprPct: 36 }],
    statement: [
      { description: "SALARY SEPTEMBER", amountInr: 120_000, credit: true },
      { description: "RENT", amountInr: 25_000, credit: false },
      { description: "SWIGGY", amountInr: 4_200, credit: false },
      { description: "CARD EMI", amountInr: 8_000, credit: false },
    ],
  });
  assert(plan.investInr === 0, "Do not invest leftover while a 36% card is open");
  assert(plan.leftoverLine.includes("loan"), "Leftover must go to the card");
  assert(!plan.headline.toLowerCase().includes("basket"), "Freedom plan is not a stock basket");

  const clean = assembleLifeFreedomPlan({
    salaryInr: 80_000,
    loans: [],
  });
  assert(clean.investInr > 0, "After the life is paid, leftover may reach Today");
  assert(clean.leftoverLine.includes("Today"), "Leftover is the only investable rupee");
  assert(
    autoFetchNote({ salaryFromProfile: true, kiteCashInr: 10722 }).includes("Kite"),
    "Auto-fetch must name Kite cash",
  );
  assert(
    autoFetchNote({ salaryFromProfile: true, kiteCashInr: 10722 }).includes("not on Zerodha"),
    "Auto-fetch must not pretend the bank is on Kite",
  );
}
