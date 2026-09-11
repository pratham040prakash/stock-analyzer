"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
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

export default function YouLifeFreedom() {
  const stored = useMemo(() => readStoredLifeFreedom(), []);
  const [salaryInr, setSalaryInr] = useState(stored.salaryInr);
  const [loans, setLoans] = useState<LifeLoan[]>(stored.loans);
  const [statement, setStatement] = useState<StatementRow[]>([]);
  const [statementNote, setStatementNote] = useState<string | null>(null);

  const plan = assembleLifeFreedomPlan({
    salaryInr,
    loans,
    statement: statement.length > 0 ? statement : undefined,
  });

  const persist = (nextSalary: number, nextLoans: LifeLoan[]) => {
    setSalaryInr(nextSalary);
    setLoans(nextLoans);
    writeStoredLifeFreedom({ salaryInr: nextSalary, loans: nextLoans });
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
        {statementNote ? (
          <p className="text-xs text-apex-muted/70">{statementNote}</p>
        ) : null}
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
