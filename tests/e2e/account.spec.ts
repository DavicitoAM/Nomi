import { test, expect } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const execute = promisify(execFile);
const python = process.platform === "win32" ? path.resolve(".venv/Scripts/python.exe") : "python";
const mailbox = path.resolve(process.env.MAILBOX_DIR ?? ".local/mailbox");

async function deliveredLink(email: string, purpose: string) {
  await execute(python, ["-m", "app.worker", "--once", "--limit", "1000"], { env: { ...process.env, MAIL_BACKEND: "file", MAILBOX_DIR: mailbox }, timeout: 30000 });
  let link = "";
  await expect.poll(async () => {
    for (const file of await readdir(mailbox)) {
      if (!file.endsWith(".json")) continue;
      const message = JSON.parse(await readFile(path.join(mailbox, file), "utf8"));
      if (message.recipient === email && message.purpose === purpose) { link = message.link; return true; }
    }
    return false;
  }).toBe(true);
  return link;
}

test("verificación y recuperación mantienen datos y revocan sesiones", async ({ page, browser }, info) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  const email = `account-${Date.now()}-${info.project.name}@example.com`;
  const originalPassword = "original-account-password";
  await page.goto("/");
  await page.getByLabel("Tu nombre").fill("Cuenta");
  await page.getByLabel("Correo electrónico").fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill(originalPassword);
  await page.getByRole("button", { name: "Crear mi espacio", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Hola, Cuenta." })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Verificación de correo" })).toBeVisible();

  const verification = await deliveredLink(email, "verify");
  await page.goto(verification);
  await expect(page.getByRole("heading", { name: "Confirma tu correo" })).toBeVisible();
  expect(new URL(page.url()).hash).toBe("");
  await page.getByRole("button", { name: "Confirmar correo", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Correo verificado");
  await page.getByRole("button", { name: "Continuar a Nomi" }).click();
  await expect(page.getByRole("heading", { name: "Hola, Cuenta." })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Verificación de correo" })).toHaveCount(0);

  await page.getByRole("button", { name: "Registrar pendiente", exact: true }).first().click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Nombre", { exact: true }).fill("Persistencia");
  await dialog.getByRole("button", { name: "Guardar contacto" }).click();
  await dialog.getByLabel("Monto", { exact: false }).fill("10000");
  await dialog.getByRole("button", { name: "Guardar pendiente" }).click();
  await expect(page.locator(".hero-stat")).toContainText("$10,000.00");

  const other = await browser.newContext();
  try {
    const oldSession = await other.request.post("http://localhost:3000/api/v1/auth/login", { headers: { Origin: "http://localhost:3000" }, data: { email, password: originalPassword } });
    expect(oldSession.status()).toBe(200);
    await page.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
    await page.getByRole("button", { name: "Inicia sesión", exact: true }).click();
    await page.getByRole("button", { name: "Olvidé mi contraseña" }).click();
    await page.getByLabel("Correo electrónico").fill(email);
    await page.getByRole("button", { name: "Enviar enlace de recuperación" }).click();
    await expect(page.getByRole("status")).toContainText("Si la cuenta puede recuperarse");
    const recovery = await deliveredLink(email, "reset");
    await page.goto(recovery);
    await expect(page.getByRole("heading", { name: "Elige una contraseña nueva" })).toBeVisible();
    expect(new URL(page.url()).hash).toBe("");
    await page.getByLabel("Nueva contraseña", { exact: true }).fill("updated-account-password");
    await page.getByLabel("Repite la contraseña").fill("updated-account-password");
    await page.getByRole("button", { name: "Guardar nueva contraseña" }).click();
    await expect(page.getByRole("status")).toContainText("Contraseña actualizada");
    expect((await other.request.get("http://localhost:3000/api/v1/me")).status()).toBe(401);
    await page.getByRole("button", { name: "Ir al inicio de sesión" }).click();
    await page.getByRole("button", { name: "Inicia sesión", exact: true }).click();
    await page.getByLabel("Correo electrónico").fill(email);
    await page.getByLabel("Contraseña", { exact: true }).fill(originalPassword);
    await page.getByRole("button", { name: "Entrar a mi espacio" }).click();
    await expect(page.getByRole("main").getByRole("alert")).toContainText("Correo o contraseña incorrectos");
    await page.getByLabel("Contraseña", { exact: true }).fill("updated-account-password");
    await page.getByRole("button", { name: "Entrar a mi espacio" }).click();
    await expect(page.locator(".hero-stat")).toContainText("$10,000.00");
    await expect(page.getByRole("button", { name: /Persistencia/ })).toBeVisible();
    await page.reload();
    await expect(page.locator(".hero-stat")).toContainText("$10,000.00");
    await page.goto(recovery);
    await page.getByLabel("Nueva contraseña", { exact: true }).fill("another-long-password");
    await page.getByLabel("Repite la contraseña").fill("another-long-password");
    await page.getByRole("button", { name: "Guardar nueva contraseña" }).click();
    await expect(page.getByRole("main").getByRole("alert")).toContainText("El enlace venció o ya fue utilizado");
    await page.screenshot({ path: `.local/nomi-account-${info.project.name}.png`, fullPage: true });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(errors).toEqual([]);
  } finally { await other.close(); }
});
