"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import {
  bankConnectHint,
  bankFetchedNote,
  bankFileConnectNote,
  rowsFromBankReview,
  type BankConsentStatus,
  type BankMonthReview,
} from "@/lib/life/bankAggregator";
import {
  assembleLifeFreedomPlan,
  ingestBankStatements,
  readStoredLifeFreedom,
  statementIngestHint,
  statementIngestNote,
  writeStoredLifeFreedom,
  type LifeLoan,
  type StatementRow,
} from "@/lib/life/financialFreedom";
import { formatInr } from "@/lib/funds";

type FreedomResponse = {
  status?: string;
  salaryInr?: number;
  needsInr?: number;
  kiteCashInr?: number;
  note?: string;
  bank?: {
    configured?: boolean;
    status?: BankConsentStatus;
    hint?: string;
    review?: BankMonthReview | null;
  };
};

export default function YouLifeFreedom() {
  const stored = useMemo(() => readStoredLifeFreedom(), []);
  const [salaryInr, setSalaryInr] = useState(stored.salaryInr);
  const [loans, setLoans] = useState<LifeLoan[]>(stored.loans);
  const [statement, setStatement] = useState<StatementRow[]>([]);
  const [statementNote, setStatementNote] = useState<string | null>(null);
  const [kiteCashInr, setKiteCashInr] = useState<number | null>(null);
  const [needsInr, setNeedsInr] = useState<number | null>(null);
  const [mobile, setMobile] = useState("");
  const [bankHint, setBankHint] = useState(bankConnectHint(false));
  const [bankConfigured, setBankConfigured] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [bankStatus, setBankStatus] = useState<BankConsentStatus>("off");
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);

  const applyFreedom = (data: FreedomResponse | null) => {
    if (!data) {
      return;
    }

    if (typeof data.kiteCashInr === "number") {
      setKiteCashInr(data.kiteCashInr);
    }
    if (typeof data.needsInr === "number" && data.needsInr > 0) {
      setNeedsInr(data.needsInr);
    }
    if (data.bank?.hint) {
      setBankHint(data.bank.hint);
    }
    setBankConfigured(Boolean(data.bank?.configured));
    if (data.bank?.status) {
      setBankStatus(data.bank.status);
    }
    if (data.bank?.review && data.bank.review.rowCount > 0) {
      setStatement(rowsFromBankReview(data.bank.review));
      setStatementNote(bankFetchedNote(data.bank.review.rowCount));
      if (data.bank.review.salaryInr > 0) {
        setSalaryInr(data.bank.review.salaryInr);
        writeStoredLifeFreedom({ salaryInr: data.bank.review.salaryInr, loans });
      }
    } else if (typeof data.salaryInr === "number" && data.salaryInr > 0 && stored.salaryInr <= 0) {
      setSalaryInr(data.salaryInr);
      writeStoredLifeFreedom({ salaryInr: data.salaryInr, loans });
    }
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const response = await apiFetch("/api/life/freedom", { cache: "no-store" });
      const data = await parseApiJson<FreedomResponse>(response, "life-freedom");
      if (!cancelled) {
        applyFreedom(data);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
    // First paint only — later polls pass the latest loans themselves.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (bankStatus !== "pending" && bankStatus !== "active") {
      return;
    }

    const started = Date.now();
    const timer = window.setInterval(() => {
      if (Date.now() - started > 90_000) {
        window.clearInterval(timer);
        return;
      }
      void apiFetch("/api/life/freedom", { cache: "no-store" }).then(async (response) => {
        applyFreedom(await parseApiJson<FreedomResponse>(response, "life-freedom"));
      });
    }, 4000);

    return () => {
      window.clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bankStatus]);

  const plan = assembleLifeFreedomPlan({
    salaryInr,
    loans,
    statement: statement.length > 0 ? statement : undefined,
    needsInr,
    kiteCashInr,
  });

  const persist = (nextSalary: number, nextLoans: LifeLoan[]) => {
    setSalaryInr(nextSalary);
    setLoans(nextLoans);
    writeStoredLifeFreedom({ salaryInr: nextSalary, loans: nextLoans });
  };

  const openBankFile = (note: string) => {
    setConnectError(note);
    fileInputRef.current?.click();
  };

  const connectBank = async () => {
    setConnecting(true);
    setConnectError(null);
    const response = await apiFetch("/api/life/bank/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile }),
    });
    const data = await parseApiJson<{ url?: string; message?: string }>(
      response,
      "bank-connect",
    );
    setConnecting(false);
    if (response.ok && data?.url) {
      window.location.assign(data.url);
      return;
    }
    openBankFile(
      response.status === 503 || !bankConfigured
        ? bankFileConnectNote()
        : (data?.message ?? bankFileConnectNote()),
    );
  };

  return (
    <section className="mb-6 space-y-4 rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-5">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Financial freedom
        </p>
        <p className="text-lg font-medium text-apex-text/95">{plan.headline}</p>
        <p className="text-sm leading-relaxed text-apex-muted/85">{plan.spendLine}</p>
        <p className="text-sm leading-relaxed text-apex-text/90">{plan.leftoverLine}</p>
        {plan.closeLoanFirst ? (
          <p className="text-sm leading-relaxed text-apex-muted/85">{plan.closeLoanFirst}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <p className="text-xs text-apex-muted/75">{bankHint}</p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={mobile}
            onChange={(event) => setMobile(event.target.value)}
            inputMode="numeric"
            autoComplete="tel"
            placeholder="Mobile on the bank account"
            className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
          />
          <button
            type="button"
            onClick={() => void connectBank()}
            disabled={connecting}
            className="rounded-lg border border-white/15 px-3 py-2 text-sm text-sky-100/90 disabled:opacity-50"
          >
            {connecting ? "Opening bank…" : "Connect bank"}
          </button>
        </div>
        {connectError ? (
          <p className="text-xs text-apex-muted/80">{connectError}</p>
        ) : null}
        {statementNote ? (
          <p className="text-xs text-apex-muted/70">{statementNote}</p>
        ) : null}
      </div>

      <label className="block space-y-1">
        <span className="text-xs text-apex-muted/75">This month&apos;s salary</span>
        <input
          type="number"
          min={0}
          value={salaryInr || ""}
          onChange={(event) => persist(Number(event.target.value) || 0, loans)}
          placeholder="₹"
          className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
        />
      </label>

      <div className="space-y-2">
        <p className="text-xs text-apex-muted/75">Loans to close</p>
        {loans.map((loan, index) => (
          <div key={`${loan.name}-${index}`} className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <input
              value={loan.name}
              onChange={(event) => {
                const next = [...loans];
                next[index] = { ...loan, name: event.target.value };
                persist(salaryInr, next);
              }}
              placeholder="Name"
              className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
            <input
              type="number"
              min={0}
              value={loan.balanceInr || ""}
              onChange={(event) => {
                const next = [...loans];
                next[index] = { ...loan, balanceInr: Number(event.target.value) || 0 };
                persist(salaryInr, next);
              }}
              placeholder="Balance"
              className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
            <input
              type="number"
              min={0}
              value={loan.emiInr || ""}
              onChange={(event) => {
                const next = [...loans];
                next[index] = { ...loan, emiInr: Number(event.target.value) || 0 };
                persist(salaryInr, next);
              }}
              placeholder="EMI"
              className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
            <input
              type="number"
              min={0}
              step="0.1"
              value={loan.aprPct || ""}
              onChange={(event) => {
                const next = [...loans];
                next[index] = { ...loan, aprPct: Number(event.target.value) || 0 };
                persist(salaryInr, next);
              }}
              placeholder="APR %"
              className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
          </div>
        ))}
        <button
          type="button"
          onClick={() =>
            persist(salaryInr, [
              ...loans,
              { name: "", balanceInr: 0, emiInr: 0, aprPct: 0 },
            ])
          }
          className="text-xs text-sky-100/80"
        >
          Add a loan
        </button>
      </div>

      <label className="block space-y-1">
        <span className="text-xs text-apex-muted/75">{statementIngestHint()}</span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt,.tsv,.xls,text/csv,text/plain"
          multiple
          onChange={(event) => {
            const files = [...(event.target.files ?? [])];
            if (files.length === 0) {
              return;
            }

            void Promise.all(files.map((file) => file.text())).then((texts) => {
              const rows = ingestBankStatements(texts);
              setStatement(rows);
              setStatementNote(statementIngestNote(rows.length, files.length));
            });
          }}
          className="block w-full text-xs text-apex-muted/75"
        />
      </label>

      {plan.investInr > 0 ? (
        <p className="text-sm text-apex-muted/80">
          {formatInr(plan.investInr)} can sit as leftover on{" "}
          <Link href="/app" className="text-sky-100/90">
            Today
          </Link>
          . Not a third name until the life is paid.
        </p>
      ) : null}
    </section>
  );
}
