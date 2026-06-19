import { test as base } from "@playwright/test";

export const USERS = {
  admin:  { email: "admin@medicia.local",  password: "AdminPass123!XYZ" },
  medico: { email: "medico@medicia.local", password: "MedicoPass123!XYZ" },
  rrhh:   { email: "rrhh@medicia.local",   password: "RrhhPass123!XYZ" },
};

export const test = base.extend<{
  loginAs: (role: keyof typeof USERS) => Promise<void>;
}>({
  loginAs: async ({ page }, use) => {
    await use(async (role) => {
      await page.goto("/login");
      await page.getByLabel(/email/i).fill(USERS[role].email);
      await page.getByLabel(/contraseña/i).fill(USERS[role].password);
      await page.getByRole("button", { name: /ingresar/i }).click();
      await page.waitForURL("/");
    });
  },
});

export { expect } from "@playwright/test";
