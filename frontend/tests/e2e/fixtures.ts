import { test as base } from "@playwright/test";

export const USERS = {
  admin:  { email: "admin",  password: "123" },
  medico: { email: "medico", password: "123" },
  rrhh:   { email: "secretaria",   password: "123" },
};

export const test = base.extend<{
  loginAs: (role: keyof typeof USERS) => Promise<void>;
}>({
  loginAs: async ({ page }, use) => {
    await use(async (role) => {
      await page.goto("/login");
      await page.getByLabel(/usuario/i).fill(USERS[role].email);
      await page.getByLabel(/clave/i).fill(USERS[role].password);
      await page.getByRole("button", { name: /ingresar/i }).click();
      await page.waitForURL("/");
    });
  },
});

export { expect } from "@playwright/test";
