#!/usr/bin/env bash
# Bootstrap Oracle Cloud (Ubuntu) VM for apex-kite-order-proxy.
# Run as root on a fresh Always Free instance in ap-mumbai-1 when possible.
set -euo pipefail

INSTALL_DIR="/opt/apex-kite-order-proxy"
SERVICE_USER="apexproxy"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash setup-oracle.sh"
  exit 1
fi

echo "==> Installing Node.js 20..."
apt-get update -qq
apt-get install -y curl ca-certificates ufw
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -d. -f1 | tr -d v)" -lt 20 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "==> Creating service user..."
id -u "${SERVICE_USER}" >/dev/null 2>&1 || useradd --system --home "${INSTALL_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"

echo "==> Installing proxy files to ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
cp server.mjs package.json "${INSTALL_DIR}/"

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  PROXY_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
  cat > "${INSTALL_DIR}/.env" <<EOF
PORT=3128
PROXY_USER=apex
PROXY_PASS=${PROXY_PASS}
EOF
  chmod 600 "${INSTALL_DIR}/.env"
  echo ""
  echo "Created ${INSTALL_DIR}/.env with a random PROXY_PASS."
  echo "Save these credentials for Vercel KITE_ORDER_PROXY_URL."
fi

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

echo "==> Installing systemd unit..."
cp kite-order-proxy.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kite-order-proxy
systemctl restart kite-order-proxy

echo "==> Configuring firewall (UFW)..."
ufw allow OpenSSH
ufw allow 3128/tcp comment "APEX Kite order proxy"
ufw --force enable

PUBLIC_IP="$(curl -fsSL https://api.ipify.org || true)"
echo ""
echo "=============================================="
echo "Proxy is running on port 3128"
echo "Public IPv4 (whitelist in Kite developer console): ${PUBLIC_IP:-unknown}"
echo "Egress check: curl http://127.0.0.1:3128/egress"
echo ""
echo "Also open TCP 3128 in Oracle Cloud → VCN → Security List → Ingress Rules"
echo "Vercel env:"
echo "  KITE_ORDER_PROXY_URL=http://apex:YOUR_PASS@${PUBLIC_IP:-YOUR_VM_IP}:3128"
echo "=============================================="
systemctl status kite-order-proxy --no-pager || true
