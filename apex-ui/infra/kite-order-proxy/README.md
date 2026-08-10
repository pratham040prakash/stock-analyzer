# Kite Order Proxy

Zerodha requires a **static whitelisted IP** for `POST /orders/*`. Vercel uses dynamic egress, so order placement routes through this tiny CONNECT proxy.

**Read-only Kite calls** (holdings, margins, trades, orders) stay on Vercel — no proxy needed.

---

## Fly.io (~$8–10/mo)

Low-ops hosting, but **not** $2/mo. Fly bills three things for this proxy:

| Item | ~Cost | Why |
|------|-------|-----|
| Always-on VM (256MB, Mumbai) | ~$2–3/mo | Proxy must run during market hours |
| Dedicated inbound IPv4 | $2/mo | Vercel reaches `:3128` over raw TCP |
| **Static egress IPv4** | **$3.60/mo** | **What Kite sees** on `POST /orders` |

**Total ≈ $8–10/mo** — the $9 you saw on Fly is in the right ballpark.

> Inbound IP ≠ egress IP on Fly. Whitelist the **`egress_ipv4`** from `curl …/egress`, not the inbound IP blindly.

### Prerequisites

1. [Fly.io account](https://fly.io/app/sign-up)
2. [Fly CLI](https://fly.io/docs/flyctl/install/): `brew install flyctl`
3. Login: `fly auth login`

### Deploy (one command)

```bash
cd apex-ui/infra/kite-order-proxy

# Optional: pick a unique app name if apex-kite-order-proxy is taken
# export FLY_APP_NAME=apex-kite-proxy-pratprak

chmod +x setup-fly.sh
./setup-fly.sh
```

The script will:

- Deploy the proxy to **Mumbai (`bom`)**
- Set `PROXY_USER` / `PROXY_PASS` secrets
- Allocate **inbound** dedicated IPv4 + **static egress** IPv4
- Print `KITE_ORDER_PROXY_URL` for Vercel

### Whitelist IP in Kite

1. Confirm egress IP:
   ```bash
   curl http://YOUR_FLY_IP:3128/egress
   ```
2. [developers.kite.trade](https://developers.kite.trade) → **Profile** → **IP Whitelist** → add that IPv4  
   (One change per calendar week — verify before saving.)

### Configure Vercel

Project → Settings → Environment Variables → **Production**:

```env
KITE_ORDER_PROXY_URL=http://apex:YOUR_PROXY_PASS@YOUR_FLY_IP:3128
```

Redeploy APEX. Only `placeZerodhaOrder` uses the proxy.

### Verify

```bash
# Proxy health
curl http://YOUR_FLY_IP:3128/health

# APEX (logged in) — proxied egress should match whitelisted IP
# Open in browser after deploy: /api/zerodha/egress-ip
```

Place a test trim from `/app` during market hours.

### Fly operations

```bash
fly logs --app apex-kite-order-proxy
fly status --app apex-kite-order-proxy
fly ips list --app apex-kite-order-proxy
fly secrets set PROXY_PASS=new_secret --app apex-kite-order-proxy
fly deploy --app apex-kite-order-proxy
```

To rotate password: update Fly secret **and** Vercel `KITE_ORDER_PROXY_URL`.

---

## Recommended if cost matters: Oracle Always Free (₹0)

Same proxy, **one public IP** for both inbound and outbound — no extra egress fee. More setup, zero monthly cost.

See `setup-oracle.sh`:

```bash
sudo bash setup-oracle.sh
```

---

## Security

- CONNECT allowed only to **`api.kite.trade:443`**
- **Basic auth** required (`PROXY_USER` / `PROXY_PASS`)
- Do not expose without credentials

## Architecture

```text
User → Vercel (APEX UI + read APIs)
              ↓  POST /orders only
         Fly.io proxy (static IPv4) → api.kite.trade
```
