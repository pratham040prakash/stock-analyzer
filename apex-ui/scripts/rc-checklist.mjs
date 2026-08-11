#!/usr/bin/env node
/**
 * v3.0.0-rc1 release checklist — prints required prod steps.
 */
console.log("APEX v3.0.0-rc1 checklist\n");
console.log("1. Supabase: npm run db:migrate:checklist — apply all ordered migrations");
console.log("2. Vercel env: ALPHA_AI_SERVICE_URL, KITE_ORDER_PROXY_URL (optional)");
console.log("3. Digest: APEX_REVIEW_DIGEST_ENABLED=true, TELEGRAM_* or APEX_DIGEST_WEBHOOK_URL");
console.log("4. Cron: CRON_SECRET set; vercel.json crons deployed");
console.log("5. GitHub secrets: APEX_VERIFY_COOKIE, APEX_E2E_COOKIE");
console.log("6. Run: npm run verify:deploy && npm run verify:prod");
console.log("7. Run: npm run test:e2e (smoke + authed with APEX_E2E_COOKIE)");
console.log("8. Tag: git tag v3.0.0-rc1 && git push origin v3.0.0-rc1\n");
