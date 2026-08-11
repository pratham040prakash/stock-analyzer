#!/usr/bin/env node
/**
 * Lists Supabase migrations in apply order and optional apply command.
 *
 * Usage:
 *   node scripts/migration-checklist.mjs
 *   node scripts/migration-checklist.mjs --apply   # requires DATABASE_URL or SUPABASE_DB_PASSWORD
 */
import { existsSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const migrationsDir = join(root, "supabase/migrations");

/** Apply after base schema; order matters for dependent columns. */
const ORDERED_MIGRATIONS = [
  "20260807_broker_connections.sql",
  "decisions_history.sql",
  "decision_memory.sql",
  "decision_memory_risk.sql",
  "decision_memory_profit.sql",
  "discipline_commits.sql",
  "user_trust_state.sql",
  "auto_trading_enabled.sql",
  "auto_trade_lock.sql",
  "premium_activations.sql",
  "decision_receipts.sql",
];

function listMigrations() {
  const onDisk = existsSync(migrationsDir)
    ? readdirSync(migrationsDir).filter((name) => name.endsWith(".sql"))
    : [];

  const ordered = ORDERED_MIGRATIONS.filter((name) => onDisk.includes(name));
  const extras = onDisk.filter((name) => !ORDERED_MIGRATIONS.includes(name)).sort();

  return {
    schema: join(root, "supabase/schema.sql"),
    ordered: ordered.map((name) => join(migrationsDir, name)),
    extras: extras.map((name) => join(migrationsDir, name)),
  };
}

function main() {
  const { schema, ordered, extras } = listMigrations();
  const apply = process.argv.includes("--apply");

  console.log("APEX Supabase migration checklist\n");
  console.log("1. Base schema (greenfield only — skip if tables exist):");
  console.log(`   ${schema}\n`);
  console.log("2. Ordered migrations:");

  ordered.forEach((file, index) => {
    console.log(`   ${String(index + 1).padStart(2, "0")}. ${file.replace(`${root}/`, "")}`);
  });

  if (extras.length > 0) {
    console.log("\n3. Additional files on disk (review manually):");
    for (const file of extras) {
      console.log(`   - ${file.replace(`${root}/`, "")}`);
    }
  }

  console.log("\nManual apply: Supabase Dashboard → SQL Editor");
  console.log(
    "Automated: npm run db:migrate -- supabase/migrations/<file>.sql",
  );
  console.log("Apply all: npm run db:migrate:all\n");

  if (apply) {
    const files = [schema, ...ordered];
    const result = spawnSync(
      "node",
      ["scripts/apply-supabase-sql.mjs", ...files],
      { cwd: root, stdio: "inherit" },
    );
    process.exit(result.status ?? 1);
  }
}

main();
