import { expect, test } from "./fixtures";

test("admin: edita tope y verifica que la celda muestra el nuevo valor", async ({ page, loginAs }) => {
  await loginAs("admin");
  await page.getByRole("link", { name: "Topes" }).click();
  await page.evaluate(() => {
    let i = 0;
    (window as any).prompt = (_msg: string, def: string) => {
      const answers = ["75", "anio-calendario", new Date().toISOString().slice(0, 10)];
      return answers[i++] ?? def;
    };
  });
  await page.getByRole("button").filter({ hasText: /—|días/ }).first().click();
  await expect(page.getByText("75 (anio-calendario)").first()).toBeVisible();
});
