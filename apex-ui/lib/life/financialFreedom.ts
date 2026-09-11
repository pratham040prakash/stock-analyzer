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

function csvNumber(value: string): number {
  const parsed = Number(value.replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

export function parseBankCsv(text: string): StatementRow[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) {
    return [];
  }

  const header = lines[0].split(",").map((cell) => cell.replace(/^"|"$/g, "").trim().toLowerCase());
  const descIdx = header.findIndex((cell) => /narr|desc|particular|remark/.test(cell));
  const debitIdx = header.findIndex((cell) => /withdraw|debit|(^| )dr( |$)/.test(cell));
  const creditIdx = header.findIndex((cell) => /deposit|credit|(^| )cr( |$)/.test(cell));
  const amountIdx = header.findIndex((cell) => /amount/.test(cell));
  const rows: StatementRow[] = [];

  for (const line of lines.slice(1)) {
    const cells = line.split(",").map((cell) => cell.replace(/^"|"$/g, "").trim());
    const description =
      (descIdx >= 0 ? cells[descIdx] : null) ??
      cells.find((cell, index) => index > 0 && /[A-Za-z]{3,}/.test(cell)) ??
      "";
    let amountInr = 0;
    let credit = false;

    if (debitIdx >= 0 || creditIdx >= 0) {
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

  return rows.slice(0, 400);
}

export function assembleLifeFreedomPlan(input: {
  salaryInr: number;
  loans: LifeLoan[];
  statement?: StatementRow[];
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
  const needs = Math.max(0, Math.round(reviewed?.needsInr ?? salary * 0.5));
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
        ? `${formatInr(investInr)} leftover is the only money Today may place.`
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
}
