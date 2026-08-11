import { test, expect } from "@playwright/test";

test.describe("APEX smoke", () => {
  test("health endpoint responds", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body).toHaveProperty("supabase");
    expect(body).toHaveProperty("env");
    expect(body).toHaveProperty("kite_proxy");
  });

  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator("body")).toContainText(/sign in|login|apex/i);
  });

  test("landing page surfaces Wait day brand", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toContainText(/Most days, Wait is the win/i);
    await expect(page.locator("body")).toContainText(/Wait · Trade · Pause/i);
  });

  test("app route guards anonymous users", async ({ page }) => {
    await page.goto("/app");
    await expect(page).toHaveURL(/\/login/);
  });

  test("portfolio route guards anonymous users", async ({ page }) => {
    await page.goto("/app/portfolio");
    await expect(page).toHaveURL(/\/login/);
  });

  test("journal route guards anonymous users", async ({ page }) => {
    await page.goto("/app/journal");
    await expect(page).toHaveURL(/\/login/);
  });

  test("review route guards anonymous users", async ({ page }) => {
    await page.goto("/app/review");
    await expect(page).toHaveURL(/\/login/);
  });

  test("planned review rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/review/planned?days=7");
    expect(response.status()).toBe(401);
  });

  test("monthly doctor rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/review/monthly");
    expect(response.status()).toBe(401);
  });

  test("ask answer rejects anonymous users", async ({ request }) => {
    const response = await request.post("/api/ask/answer", {
      data: { question: "Should I buy RELIANCE?" },
    });
    expect(response.status()).toBe(401);
  });

  test("quarterly review rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/review/quarterly");
    expect(response.status()).toBe(401);
  });

  test("new capital rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/capital/new");
    expect(response.status()).toBe(401);
  });

  test("today brief rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/today/brief");
    expect(response.status()).toBe(401);
  });

  test("portfolio overview rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/portfolio/overview");
    expect(response.status()).toBe(401);
  });

  test("research summary rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/research/summary?symbol=RELIANCE");
    expect(response.status()).toBe(401);
  });

  test("you snapshot rejects anonymous users", async ({ request }) => {
    const response = await request.get("/api/you/snapshot");
    expect(response.status()).toBe(401);
  });

  test("you route guards anonymous users", async ({ page }) => {
    await page.goto("/app/you");
    await expect(page).toHaveURL(/\/login/);
  });

  test("explore route guards anonymous users", async ({ page }) => {
    await page.goto("/app/explore");
    await expect(page).toHaveURL(/\/login/);
  });

  test("settings route guards anonymous users", async ({ page }) => {
    await page.goto("/app/you/settings");
    await expect(page).toHaveURL(/\/login/);
  });

  test("review digest cron rejects anonymous callers", async ({ request }) => {
    const response = await request.get("/api/cron/review-digest");
    expect(response.status()).toBe(401);
  });

  test("trust route guards anonymous users", async ({ page }) => {
    await page.goto("/app/trust");
    await expect(page).toHaveURL(/\/login/);
  });
});
