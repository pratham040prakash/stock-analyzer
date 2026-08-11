# Alpha AI Worker

Hosts `build_alpha_ai_report` over HTTP so Vercel can call research without local Python.

## Endpoints

| Path | Description |
|------|-------------|
| `GET /health` | Liveness |
| `GET /summary?symbol=RELIANCE` | Alpha AI JSON payload |

## Deploy (Fly.io example)

From repository root:

```bash
fly launch --config apex-ui/infra/alpha-ai-worker/fly.toml --no-deploy
fly deploy --config apex-ui/infra/alpha-ai-worker/fly.toml
```

Set on Vercel:

```bash
ALPHA_AI_SERVICE_URL=https://your-alpha-worker.fly.dev
```

## Local smoke

```bash
python apex-ui/infra/alpha-ai-worker/server.py
curl "http://127.0.0.1:8080/summary?symbol=RELIANCE"
```
