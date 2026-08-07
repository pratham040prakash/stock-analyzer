#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apex-ui"

npm run build

# When distDir is ../.next, output is already at repo root.
if [[ -f "$ROOT/.next/routes-manifest.json" ]]; then
  echo "OK: routes-manifest.json at repo root"
  exit 0
fi

# Fallback copy if distDir redirect did not apply.
if [[ -f "$ROOT/apex-ui/.next/routes-manifest.json" ]]; then
  rm -rf "$ROOT/.next"
  cp -R "$ROOT/apex-ui/.next" "$ROOT/.next"
  echo "OK: copied apex-ui/.next to repo root"
  exit 0
fi

echo "ERROR: routes-manifest.json not found after build"
ls -la "$ROOT/.next" 2>/dev/null || echo "  (no $ROOT/.next)"
ls -la "$ROOT/apex-ui/.next" 2>/dev/null || echo "  (no $ROOT/apex-ui/.next)"
exit 1
