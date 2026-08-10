#!/usr/bin/env bash
# Deploy apex-kite-order-proxy to Fly.io with static egress for Kite whitelisting.
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="${FLY_APP_NAME:-apex-kite-order-proxy}"
REGION="${FLY_REGION:-bom}"

if ! command -v fly >/dev/null 2>&1; then
  echo "Install Fly CLI first: https://fly.io/docs/flyctl/install/"
  exit 1
fi

if ! fly auth whoami >/dev/null 2>&1; then
  echo "Log in: fly auth login"
  exit 1
fi

PROXY_PASS="${PROXY_PASS:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)}"

echo "==> Ensuring Fly app ${APP_NAME} exists..."
if ! fly apps list | grep -q "${APP_NAME}"; then
  fly apps create "${APP_NAME}" --org personal
fi

echo "==> Setting proxy credentials..."
fly secrets set \
  PROXY_USER=apex \
  PROXY_PASS="${PROXY_PASS}" \
  --app "${APP_NAME}"

echo "==> Deploying (region: ${REGION})..."
fly deploy --app "${APP_NAME}"

echo "==> Allocating dedicated inbound IPv4 (~\$2/mo — Vercel connects here on :3128)..."
if ! fly ips list --app "${APP_NAME}" | grep -q "v4.*public"; then
  fly ips allocate-v4 --app "${APP_NAME}" --region "${REGION}" 2>/dev/null || \
    fly ips allocate-v4 --app "${APP_NAME}"
fi

echo "==> Allocating static egress IPv4 (~\$3.60/mo — whitelist THIS in Kite)..."
if ! fly ips list --app "${APP_NAME}" | grep -qi "egress"; then
  fly ips allocate-egress --app "${APP_NAME}" -r "${REGION}"
fi

INBOUND_IP="$(fly ips list --app "${APP_NAME}" | awk '/v4/ && !/egress/ {print $1; exit}')"

echo ""
echo "=============================================="
echo "Fly proxy deployed (~\$8–10/mo total — see README)"
echo ""
echo "Inbound IP (Vercel KITE_ORDER_PROXY_URL host): ${INBOUND_IP:-run: fly ips list}"
echo ""
echo "Vercel → Settings → Environment Variables:"
echo "  KITE_ORDER_PROXY_URL=http://apex:${PROXY_PASS}@${INBOUND_IP:-YOUR_FLY_INBOUND_IP}:3128"
echo ""
echo "Kite whitelist — use egress IP from /egress (NOT always same as inbound):"
echo "  curl http://${INBOUND_IP:-YOUR_FLY_INBOUND_IP}:3128/egress"
echo ""
echo "  developers.kite.trade → Profile → IP Whitelist → egress_ipv4 from above"
echo "=============================================="
