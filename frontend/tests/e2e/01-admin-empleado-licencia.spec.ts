import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures";

test("admin: crea empleado, abre licencia y la envía", async ({ page, loginAs }) => {
  await loginAs("admin");
  await page.getByRole("link", { name: "Empleados" }).click();
  await page.getByRole("link", { name: "Nuevo" }).click();

  const stamp = Date.now().toString();
  await page.getByLabel(/legajo/i).fill(`L${stamp.slice(-6)}`);
  await page.getByLabel(/cuil/i).fill("20111111119");
  await page.getByLabel(/apellido/i).fill("Test");
  await page.getByLabel(/nombre/i).fill("Empleado");
  await page.getByLabel(/fecha de ingreso/i).fill("2022-01-15");
  await page.getByLabel(/categoría/i).selectOption({ label: "Planta permanente" });
  await page.getByRole("button", { name: /guardar/i }).click();
  await expect(page).toHaveURL(/\/empleados$/);

  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("link", { name: "Nueva" }).click();
  await page.getByLabel(/empleado/i).selectOption({ index: 1 });
  await page.getByLabel(/tipo/i).selectOption({ label: "Enfermedad común" });
  await page.getByLabel(/desde/i).fill("2026-06-01");
  await page.getByLabel(/hasta/i).fill("2026-06-05");
  await page.getByRole("button", { name: /guardar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("borrador");
  await page.getByRole("button", { name: /enviar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("enviado");

  const a = await new AxeBuilder({ page }).analyze();
  expect(a.violations.filter((v) => v.impact === "serious" || v.impact === "critical")).toEqual([]);
});
