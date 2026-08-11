#!/usr/bin/env node
/**
 * v3.0.0-rc1 release checklist — prints required prod steps.
 * Pass --verify to exit non-zero when required local gates fail.
 */
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const verifyMode = process.argv.includes("--verify");
const root = join(dirname(fileURLToPath(import.meta.url)), "..");

const requiredMigrationFiles = [
  "decision_receipts.sql",
  "discipline_commits.sql",
  "investment_thesis.sql",
  "operating_profile.sql",
  "user_trust_state.sql",
];

console.log("APEX v3.0.0-rc1 checklist\n");
console.log("Sprints W–Y shipped:");
console.log("  W — Broker polish (hold/skip trim, silent P&L, breakout guard)");
console.log("  X — RC verification (cron auth, e2e, verify:prod)");
console.log("  Y — Soak doc + roadmap v0.9 (tag after prod verify)\n");
console.log("1. Supabase: npm run db:migrate:checklist — apply all ordered migrations");
console.log("2. Vercel env: ALPHA_AI_SERVICE_URL, KITE_ORDER_PROXY_URL (optional)");
console.log("3. Digest: APEX_REVIEW_DIGEST_ENABLED=true, TELEGRAM_* or APEX_DIGEST_WEBHOOK_URL");
console.log("4. Cron: CRON_SECRET set; vercel.json crons deployed");
console.log("5. GitHub secrets: APEX_VERIFY_COOKIE, APEX_E2E_COOKIE");
console.log("6. Run: npm run verify:deploy && npm run verify:prod");
console.log("7. Run: npm run test:e2e (smoke + authed with APEX_E2E_COOKIE)");
console.log("8. Tag: git tag v3.0.0-rc1 && git push origin v3.0.0-rc1\n");

if (!verifyMode) {
  process.exit(0);
}

const failures = [];

for (const file of requiredMigrationFiles) {
  const path = join(root, "supabase", "migrations", file);
  if (!existsSync(path)) {
    failures.push(`Missing migration: ${file}`);
  }
}

const keyModules = [
  "lib/sellTrim.ts",
  "services/review/runReviewDigestCron.ts",
  "app/api/cron/review-digest/route.ts",
];

for (const relative of keyModules) {
  if (!existsSync(join(root, relative))) {
    failures.push(`Missing module: ${relative}`);
  }
}

if (failures.length > 0) {
  console.error("RC verify failed:");
  for (const failure of failures) {
    console.error(`  - ${failure}`);
  }
  process.exit(1);
}

console.log("RC verify OK — required modules and migrations present.\n");
process.exit(0);
