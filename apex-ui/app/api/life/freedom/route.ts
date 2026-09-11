import { apiError, apiOk } from "@/lib/api/response";
import {
  bankConnectHint,
  readSetuConfig,
  rowsFromBankReview,
} from "@/lib/life/bankAggregator";
import {
  assembleLifeFreedomPlan,
  autoFetchNote,
} from "@/lib/life/financialFreedom";
import {
  getExpenseMidpoint,
  getIncomeMidpoint,
} from "@/lib/financialProfile";
import { fetchZerodhaFundsForUser } from "@/services/broker/funds";
import { readLifeBankConsent } from "@/services/life/bankStore";
import { getFinancialProfileFromDb } from "@/services/portfolio/repository";
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

  const [profile, funds, bank] = await Promise.all([
    getFinancialProfileFromDb(supabase, user.id),
    fetchZerodhaFundsForUser(supabase, user.id),
    readLifeBankConsent(supabase, user.id),
  ]);

  const salaryInr = profile ? getIncomeMidpoint(profile.incomeRange) : 0;
  const needsInr = profile ? getExpenseMidpoint(profile.expenseRange) : 0;
  const kiteCashInr = funds.status === "OK" ? funds.margins.marginAvailable : 0;
  const configured = readSetuConfig().configured;
  const statement = bank?.review ? rowsFromBankReview(bank.review) : undefined;
  const plan = assembleLifeFreedomPlan({
    salaryInr,
    loans: [],
    statement,
    needsInr,
    kiteCashInr,
  });

  return apiOk({
    salaryInr: statement && plan.salaryInr > 0 ? plan.salaryInr : salaryInr,
    needsInr: statement && plan.needsInr > 0 ? plan.needsInr : needsInr,
    kiteCashInr,
    note: autoFetchNote({
      salaryFromProfile: Boolean(profile),
      kiteCashInr,
    }),
    bank: {
      configured,
      status: configured ? (bank?.status ?? "off") : "off",
      hint: bankConnectHint(configured),
      review: bank?.review ?? null,
    },
    plan,
  });
}
