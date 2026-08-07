This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

This app lives in the **`apex-ui/`** subdirectory of the monorepo.

### Recommended (simplest)

1. Vercel → **Project Settings → General → Root Directory** → set to **`apex-ui`**
2. Add environment variables from `.env.example`
3. Redeploy

### Alternative (repo root as Vercel root)

The repo root includes `vercel.json` and `package.json` that run `cd apex-ui && npm run build` when Root Directory is left blank.

### Required env vars

See `apex-ui/.env.example` — include `NEXT_PUBLIC_APP_URL`, Supabase keys, Zerodha keys, `TOKEN_ENCRYPTION_KEY`, and `CRON_SECRET`.

### Verify deploy

`GET /api/health` should return `{ "supabase": "connected", "env": "ok" }`.

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
