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
  "premium_subscriptions.sql",
  "premium_trial_offers.sql",
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
  "app/api/subscription/webhook/razorpay/route.ts",
  "app/api/subscription/trial/route.ts",
  "services/subscription/razorpayConfig.ts",
  "services/subscription/conversionFunnel.ts",
  "lib/supabase/migrationHealth.ts",
  "lib/gtm/waitDayBrandCopy.ts",
  "lib/gtm/kiteConnectDisciplineCopy.ts",
  "components/onboarding/KiteConnectDisciplineCard.tsx",
  "lib/gtm/advisorPilotCopy.ts",
  "services/review/assembleAdvisorReviewPack.ts",
  "app/api/review/advisor-pack/route.ts",
  "components/review/AdvisorReviewPilotPanel.tsx",
  "lib/gtm/spouseReviewInviteCopy.ts",
  "services/review/assembleSpouseReviewInvite.ts",
  "app/api/review/spouse-invite/route.ts",
  "components/review/SpouseReviewInvitePanel.tsx",
  "lib/gtm/esopReviewPersonaCopy.ts",
  "services/review/assembleEsopReviewBrief.ts",
  "app/api/review/esop-brief/route.ts",
  "components/review/EsopReviewPersonaPanel.tsx",
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

console.log("--- v3.1.0 (T2 + T3-1) ---");
console.log("See docs/product/APEX_V3_1_SOAK.md before tagging v3.1.0");
console.log("Premium modules:");
console.log("  lib/subscription/premiumCopy.ts");
console.log("  components/subscription/PremiumValueCard.tsx");
console.log("  components/subscription/PremiumCheckoutPanel.tsx");
console.log("  services/subscription/requirePremiumFeature.ts");
console.log("  services/subscription/razorpayConfig.ts");
console.log("  app/api/subscription/webhook/razorpay/route.ts\n");

console.log("--- v3.2.0 (T3 monetization) ---");
console.log("See docs/product/APEX_V3_2_SOAK.md before tagging v3.2.0");
console.log("Apply migrations: premium_subscriptions.sql, premium_trial_offers.sql");
console.log("Trial funnel:");
console.log("  services/subscription/conversionFunnel.ts");
console.log("  app/api/subscription/trial/route.ts");
console.log("  components/subscription/PremiumTrialOfferCard.tsx");
console.log("Health probes: lib/supabase/migrationHealth.ts");
console.log("Tag: git tag v3.2.0 && git push origin v3.2.0\n");

console.log("--- T4a (Wait day GTM) ---");
console.log("Brand copy: lib/gtm/waitDayBrandCopy.ts");
console.log("Landing + OG: components/landing/LandingHero.tsx, app/page.tsx");
console.log("In-app: components/you/HowApexWorksClient.tsx\n");

console.log("--- T4b (Kite connect discipline) ---");
console.log("Copy: lib/gtm/kiteConnectDisciplineCopy.ts");
console.log("Connect card: components/ConnectZerodhaCard.tsx");
console.log("Post-connect welcome: components/onboarding/KiteConnectDisciplineCard.tsx\n");

console.log("--- T4c (Advisor B2B pilot) ---");
console.log("Enable: APEX_ADVISOR_PILOT_ENABLED=true · APEX_ADVISOR_PILOT_SEATS=1");
console.log("Pack API: app/api/review/advisor-pack/route.ts");
console.log("UI: components/review/AdvisorReviewPilotPanel.tsx\n");

console.log("--- T4d (Spouse review invite) ---");
console.log("Disable: APEX_SPOUSE_REVIEW_INVITE_ENABLED=false");
console.log("Invite API: app/api/review/spouse-invite/route.ts");
console.log("UI: components/review/SpouseReviewInvitePanel.tsx\n");

console.log("--- T4e (ESOP review persona) ---");
console.log("Disable: APEX_ESOP_REVIEW_PERSONA_ENABLED=false");
console.log("Brief API: app/api/review/esop-brief/route.ts");
console.log("UI: components/review/EsopReviewPersonaPanel.tsx\n");

console.log("--- T4f (Phase T4 release prep) ---");
console.log("See docs/product/APEX_V3_T4_SOAK.md before closing Phase T4");
console.log("Prod verify: advisor-pack, spouse-invite, esop-brief auth probes");
console.log("Release index: docs/product/APEX_V3_RELEASE_INDEX.md\n");

console.log("--- T5a (Scale path metrics) ---");
console.log("Health: GET /api/health → scale_path (paying subs, trials, T4-6 targets)");
console.log("T4-6 (15k paying / ARR) is a business milestone — not a deploy gate\n");

process.exit(0);
