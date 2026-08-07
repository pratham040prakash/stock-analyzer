#!/usr/bin/env node
/**
 * Apply Supabase SQL files using a direct Postgres connection.
 *
 * Required in apex-ui/.env.local (or env):
 *   SUPABASE_DB_PASSWORD=<database password from Supabase Dashboard → Settings → Database>
 * Optional:
 *   DATABASE_URL=postgresql://postgres.[ref]:[password]@... (overrides constructed URL)
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const envPath = join(root, ".env.local");

function loadEnvFile(path) {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    if (!(key in process.env)) process.env[key] = value;
  }
}

loadEnvFile(envPath);

const projectRef = "wmgnwujrtsmtchuhcfzk";
const region = "ap-south-1";

function resolveDatabaseUrl() {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;

  const password = process.env.SUPABASE_DB_PASSWORD;
  if (!password) {
    console.error(
      [
        "Missing database credentials.",
        "",
        "Add one of these to apex-ui/.env.local:",
        "  SUPABASE_DB_PASSWORD=<password from Supabase Dashboard → Project Settings → Database>",
        "  DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres",
        "",
        "Or run the SQL manually:",
        `  https://supabase.com/dashboard/project/${projectRef}/sql/new`,
      ].join("\n")
    );
    process.exit(1);
  }

  const encoded = encodeURIComponent(password);
  return `postgresql://postgres.${projectRef}:${encoded}@aws-0-${region}.pooler.supabase.com:6543/postgres`;
}

async function main() {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    files.push(
      join(root, "supabase/schema.sql"),
      join(root, "supabase/migrations/20260807_broker_connections.sql")
    );
  }

  const postgres = (await import("postgres")).default;
  const sql = postgres(resolveDatabaseUrl(), { ssl: "require", max: 1 });

  try {
    for (const file of files) {
      const body = readFileSync(file, "utf8");
      console.log(`Applying ${file}...`);
      await sql.unsafe(body);
      console.log(`OK: ${file}`);
    }
    console.log("All SQL applied successfully.");
  } finally {
    await sql.end({ timeout: 5 });
  }
}

main().catch((err) => {
  console.error("Migration failed:", err.message ?? err);
  process.exit(1);
});
