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

  const player = page.locator(".historical-player-shell");
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
