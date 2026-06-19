import { expect, test } from "./fixtures";

test("médico: rechaza licencia con motivo", async ({ page, loginAs }) => {
  await loginAs("medico");
  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("combobox").first().selectOption("enviado");
  await page.getByRole("link", { name: /detalle/i }).first().click();
  await page.evaluate(() => { (window as any).prompt = () => "certificado ilegible"; });
  await page.getByRole("button", { name: /rechazar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("rechazado");
});
