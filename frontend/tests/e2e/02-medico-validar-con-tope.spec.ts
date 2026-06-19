import { expect, test } from "./fixtures";

test("médico: valida licencia y ve warning si excede tope", async ({ page, loginAs }) => {
  await loginAs("medico");
  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("combobox").first().selectOption("enviado");
  const detalle = page.getByRole("link", { name: /detalle/i }).first();
  await detalle.click();

  // Stub prompt() before pressing Validar (the inline button uses window.prompt).
  await page.evaluate(() => { (window as any).prompt = () => "30"; });
  await page.getByRole("button", { name: /validar/i }).click();

  await expect(page.getByText("Estado:")).toContainText("validado");
});
