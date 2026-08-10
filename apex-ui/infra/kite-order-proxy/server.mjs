/**
 * Restricted CONNECT proxy — only api.kite.trade:443.
 * Run on Oracle Cloud (or any VPS) with a static public IPv4.
 *
 * Whitelist that IPv4 in developers.kite.trade → Profile → IP Whitelist.
 * Set on Vercel: KITE_ORDER_PROXY_URL=http://USER:PASS@YOUR_VM_IP:3128
 */
import http from "node:http";
import net from "node:net";

const PORT = Number(process.env.PORT ?? 3128);
const PROXY_USER = process.env.PROXY_USER?.trim() ?? "";
const PROXY_PASS = process.env.PROXY_PASS?.trim() ?? "";
const ALLOWED_HOST = "api.kite.trade";

function unauthorized(res) {
  res.writeHead(407, {
    "Proxy-Authenticate": 'Basic realm="kite-order-proxy"',
  });
  res.end("Proxy authentication required");
}

function checkAuth(req) {
  if (!PROXY_USER || !PROXY_PASS) {
    console.warn(
      "WARNING: PROXY_USER/PROXY_PASS not set — proxy accepts any client.",
    );
    return true;
  }

  const header = req.headers["proxy-authorization"];
  if (!header?.startsWith("Basic ")) {
    return false;
  }

  const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
  const separator = decoded.indexOf(":");
  if (separator < 0) {
    return false;
  }

  const user = decoded.slice(0, separator);
  const pass = decoded.slice(separator + 1);
  return user === PROXY_USER && pass === PROXY_PASS;
}

async function handleEgress(res) {
  try {
    const response = await fetch("https://api.ipify.org?format=json", {
      signal: AbortSignal.timeout(10_000),
    });
    const payload = await response.json();

    res.writeHead(200, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        egress_ipv4: payload.ip ?? null,
        allowed_host: ALLOWED_HOST,
        port: PORT,
      }),
    );
  } catch (error) {
    res.writeHead(500, { "content-type": "text/plain" });
    res.end(error instanceof Error ? error.message : "egress lookup failed");
  }
}

function handleConnect(req, res) {
  if (!checkAuth(req)) {
    unauthorized(res);
    return;
  }

  const target = req.url ?? "";
  const [host, portText] = target.split(":");
  const port = Number(portText || 443);

  if (host !== ALLOWED_HOST || !Number.isFinite(port) || port <= 0) {
    res.writeHead(403, { "content-type": "text/plain" });
    res.end(`Forbidden host — only ${ALLOWED_HOST}:443 is allowed`);
    return;
  }

  const upstream = net.connect(port, host, () => {
    res.writeHead(200, "Connection Established");
    res.end();
    upstream.pipe(req.socket);
    req.socket.pipe(upstream);
  });

  upstream.on("error", () => {
    if (!res.headersSent) {
      res.writeHead(502, { "content-type": "text/plain" });
    }
    res.end("Upstream connection failed");
  });

  req.socket.on("error", () => {
    upstream.destroy();
  });
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "content-type": "text/plain" });
    res.end("ok");
    return;
  }

  if (req.method === "GET" && req.url === "/egress") {
    void handleEgress(res);
    return;
  }

  if (req.method === "CONNECT") {
    handleConnect(req, res);
    return;
  }

  res.writeHead(405, { "content-type": "text/plain" });
  res.end("Use CONNECT for Kite orders, or GET /egress for whitelist IP");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(
    `kite-order-proxy listening on 0.0.0.0:${PORT} → ${ALLOWED_HOST}:443 only`,
  );
});
