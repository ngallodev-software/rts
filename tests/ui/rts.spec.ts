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
