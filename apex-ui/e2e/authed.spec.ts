import { test, expect } from "@playwright/test";

const sessionCookie = process.env.APEX_E2E_COOKIE?.trim();

test.describe("APEX authenticated smoke", () => {
  test.skip(!sessionCookie, "Set APEX_E2E_COOKIE for authenticated smoke tests");

  test.use({
    extraHTTPHeaders: {
      Cookie: sessionCookie ?? "",
    },
  });

  test("today brief returns decision envelope", async ({ request }) => {
    const response = await request.get("/api/today/brief");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.decision).toBeTruthy();
    expect(body.trust).toBeTruthy();
  });

  test("review reconcile accepts session", async ({ request }) => {
    const response = await request.post("/api/review/reconcile");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(typeof body.synced).toBe("boolean");
    expect(typeof body.status).toBe("string");
  });

  test("planned vs actual returns rows", async ({ request }) => {
    const response = await request.get("/api/review/planned?days=14");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(Array.isArray(body.rows)).toBeTruthy();
    expect(body.summary).toBeTruthy();
  });

  test("monthly doctor returns view model", async ({ request }) => {
    const response = await request.get("/api/review/monthly");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.doctor).toBeTruthy();
  });

  test("receipts list returns array", async ({ request }) => {
    const response = await request.get("/api/receipts?days=7");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(Array.isArray(body.receipts)).toBeTruthy();
  });

  test("ask answer returns one-shot response", async ({ request }) => {
    const response = await request.post("/api/ask/answer", {
      data: { question: "Should I buy RELIANCE?" },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.answer?.answer_word).toMatch(/Buy|Wait|Pass/);
  });

  test("portfolio ask handles concentration question", async ({ request }) => {
    const response = await request.post("/api/ask/answer", {
      data: { question: "Am I too concentrated?" },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.answer?.answer_word).toMatch(/Buy|Wait|Pass/);
  });

  test("quarterly review returns view model", async ({ request }) => {
    const response = await request.get("/api/review/quarterly");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.quarterly).toBeTruthy();
  });

  test("new capital workflow returns envelope", async ({ request }) => {
    const response = await request.get("/api/capital/new");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.workflow).toBeTruthy();
  });

  test("funds endpoint returns envelope for signed-in user", async ({ request }) => {
    const response = await request.get("/api/funds");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(["OK", "NOT_CONNECTED", "TOKEN_EXPIRED", "ERROR", "PARTIAL"]).toContain(
      body.status,
    );
  });

  test("discipline streak accepts WAIT commit", async ({ request }) => {
    const response = await request.post("/api/discipline/streak", {
      data: { intent: "protect", action: "WAIT", stock: "RELIANCE" },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.streak).toBeTruthy();
  });

  test("operating profile returns envelope", async ({ request }) => {
    const response = await request.get("/api/operating-profile");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(typeof body.complete).toBe("boolean");
    expect(body.profile === null || typeof body.profile?.investmentStyle === "string").toBeTruthy();
  });

  test("today brief includes daily verdict", async ({ request }) => {
    const response = await request.get("/api/today/brief");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(["wait", "trade", "pause"]).toContain(body.decision?.daily_verdict);
  });

  test("how it works page loads for signed-in user", async ({ page }) => {
    await page.goto("/app/you/how-it-works");
    await expect(page).toHaveURL(/\/app\/you\/how-it-works/);
    await expect(page.locator("body")).toContainText(/How APEX works/i);
    await expect(page.locator("body")).toContainText(/Wait · Trade · Pause/i);
  });

  test("review page loads for signed-in user", async ({ page }) => {
    await page.goto("/app/review");
    await expect(page).toHaveURL(/\/app\/review/);
    await expect(page.locator("body")).toContainText(/Weekly review|review/i);
  });

  test("macro ask handles index question", async ({ request }) => {
    const response = await request.post("/api/ask/answer", {
      data: { question: "What if Nifty falls 2%?" },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.answer?.answer_word).toMatch(/Buy|Wait|Pass|Reduce/);
  });

  test("contextual lesson returns envelope", async ({ request }) => {
    const response = await request.get("/api/learning/contextual");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
  });

  test("thesis export returns markdown", async ({ request }) => {
    const response = await request.get("/api/thesis/export");
    expect(response.ok()).toBeTruthy();

    const text = await response.text();
    expect(text).toContain("Investment Book");
  });

  test("thesis watch returns warnings array", async ({ request }) => {
    const response = await request.get("/api/thesis/watch");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(Array.isArray(body.warnings)).toBeTruthy();
  });

  test("review digest GET returns envelope", async ({ request }) => {
    const response = await request.get("/api/review/digest");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.digest).toBeTruthy();
  });

  test("settings page loads for signed-in user", async ({ page }) => {
    await page.goto("/app/you/settings");
    await expect(page).toHaveURL(/\/app\/you\/settings/);
    await expect(page.locator("body")).toContainText(/Settings/i);
  });

  test("affordability ask handles portfolio question", async ({ request }) => {
    const response = await request.post("/api/ask/answer", {
      data: { question: "Can I afford this trade?" },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("ok");
    expect(body.answer?.answer_word).toMatch(/Buy|Wait|Pass|Reduce/);
  });

  test("explore page loads for signed-in user", async ({ page }) => {
    await page.goto("/app/explore");
    await expect(page).toHaveURL(/\/app\/explore/);
    await expect(page.locator("body")).toContainText(/Explore/i);
  });

  test("journal redirects into review receipts tab", async ({ page }) => {
    await page.goto("/app/journal");
    await expect(page).toHaveURL(/\/app\/review\?tab=receipts/);
  });
});
