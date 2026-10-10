import { expect, test } from "@playwright/test";

test("designer renders and a manifest export is requested through /rts/api", async ({ page }) => {
  await page.route("**/rts/api/export", async (route) => {
    const payload = route.request().postDataJSON();
    expect(payload.artifactKey).toBe("manifest");
    await route.fulfill({
      contentType: "application/zip",
      headers: { "content-disposition": 'attachment; filename="manifest-json.zip"' },
      body: "test export",
    });
  });

  await page.goto("/rts/");
  await expect(page.getByRole("heading", { name: "Parametric rocket tooling drawings" })).toBeVisible();
  await expect(page.getByRole("img", { name: /BP Core burner/i })).toBeVisible();
  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(page.locator(".app-shell")).toHaveClass(/theme-dark/);

  await page.getByRole("button", { name: "Exports" }).click();
  await expect(page.getByText("Export center")).toBeVisible();

  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Manifest ZIP" }).click();
  expect((await download).suggestedFilename()).toBe("manifest-json.zip");
});

test("historical SWF offers drawing-only and full-page printing", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1200 });
  await page.addInitScript(() => {
    window.print = () => undefined;
  });
  await page.goto("/rts/");
  await page.getByRole("button", { name: "Historical tools" }).click();

  const ruffle = page.locator("ruffle-player");
  await expect(ruffle).toBeVisible();
  await expect.poll(async () => (await ruffle.boundingBox())?.height).toBe(720);
  const player = page.getByLabel("Original Rocket Tool Sketcher Flash application", { exact: true });
  const bounds = await player.boundingBox();
  expect(bounds).not.toBeNull();
  const scale = Math.min(bounds!.width / 1140, bounds!.height / 720);
  const stageLeft = bounds!.x + (bounds!.width - 1140 * scale) / 2;
  const stageTop = bounds!.y + (bounds!.height - 720 * scale) / 2;
  await player.dispatchEvent("click", {
    clientX: stageLeft + 1090 * scale,
    clientY: stageTop + 642 * scale,
  });
  await expect(page.getByRole("dialog", { name: "Print Rocket Tool Sketcher" })).toBeVisible();
  await page.getByRole("button", { name: /Drawing only/ }).click();
  await expect(page.locator(".historical-layout")).toHaveClass(/print-swf-drawing/);

  await page.getByRole("button", { name: "Print…" }).click();
  await page.getByRole("button", { name: /Whole SWF page/ }).click();
  await expect(page.locator(".historical-layout")).toHaveClass(/print-swf-full/);
});

test("one-column helper artwork stays in flow below the input instead of covering fields", async ({ page }) => {
  await page.setViewportSize({ width: 760, height: 900 });
  await page.goto("/rts/");
  const fields = page.locator(".helper-field");
  const first = fields.first();
  await first.hover();
  const inlineHelp = first.locator(".helper-inline");
  await expect(inlineHelp).toBeVisible();
  await expect(page.locator(".helper-layer")).toBeHidden();
  const inputBox = await first.locator("input").boundingBox();
  const helperBox = await inlineHelp.boundingBox();
  const nextBox = await fields.nth(1).boundingBox();
  expect(inputBox && helperBox && nextBox).toBeTruthy();
  expect(helperBox!.y).toBeGreaterThanOrEqual(inputBox!.y + inputBox!.height);
  expect(nextBox!.y).toBeGreaterThanOrEqual(helperBox!.y + helperBox!.height);
});

test("mobile drawings stay readable, scroll within the page, and offer a whole-sheet view", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  await page.goto("/rts/");

  for (const view of ["Designer", "Exports"]) {
    await page.getByRole("button", { name: view, exact: true }).click();
    const viewer = page.getByRole("region", { name: /drawing viewer/ });
    await expect.poll(() => page.locator(".rts-dim-text").first().evaluate((text) => {
      const matrix = (text as SVGGraphicsElement).getScreenCTM()!;
      return Math.round(parseFloat(getComputedStyle(text).fontSize) * Math.hypot(matrix.a, matrix.b) * 100) / 100;
    })).toBeGreaterThanOrEqual(12);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
    await viewer.evaluate((element) => { element.scrollLeft = 300; });
    await expect.poll(() => viewer.evaluate((element) => element.scrollLeft)).toBe(300);
    await page.getByRole("button", { name: "Fit whole drawing" }).click();
    await expect.poll(() => viewer.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);
    await page.getByRole("button", { name: "Readable size" }).click();
    await expect.poll(() => viewer.evaluate((element) => element.scrollWidth)).toBeGreaterThan(390);
  }

  await page.getByRole("button", { name: "Historical tools" }).click();
  const player = page.locator("ruffle-player");
  await expect(player).toBeVisible();
  expect((await player.boundingBox())?.height).toBe(720);
  const shell = page.locator(".historical-player-shell");
  await page.getByRole("button", { name: "Controls", exact: true }).click();
  await expect.poll(() => shell.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Drawing", exact: true }).click();
  await expect.poll(() => shell.evaluate((element) => element.scrollLeft)).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await context.close();
});
