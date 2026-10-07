import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

async function account(page: Page, label: string) {
  const email = `${label}-${crypto.randomUUID()}@example.com`;
  const password = "local-quality-password-2026";
  await page.goto("/");
  await page.getByLabel("Tu nombre").fill("Pruebas");
  await page.getByLabel("Correo electrónico").fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Crear mi espacio", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Hola, Pruebas." })).toBeVisible();
  return { email, password };
}

async function seed(page: Page) {
  const csrf = (await page.context().cookies()).find(c => c.name === "nomi_csrf")!.value;
  const headers = { Origin: "http://localhost:3000", "X-CSRF-Token": csrf };
  const contact = await page.request.post("/api/v1/contacts", { headers, data: { name: "Contacto prueba" } });
  expect(contact.status()).toBe(201);
  const c = await page.request.post("/api/v1/commitments", { headers: { ...headers, "Idempotency-Key": crypto.randomUUID() }, data: { contact_id: (await contact.json()).id, direction: "receivable", original_amount_minor: 1000000, currency_code: "MXN" } });
  expect(c.status()).toBe(201);
  await page.reload();
  return { commitment: await c.json(), headers };
}

async function openPayment(page: Page) {
  await page.getByRole("button", { name: /Contacto prueba/ }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Registrar abono", exact: true }).click();
  await page.getByRole("dialog").getByLabel("Monto del abono").fill("2500");
}

test("contactos, edición, cancelación, exportación y accesibilidad", async ({ page }, info) => {
  test.setTimeout(90000);
  await account(page, "lifecycle");
  await seed(page);
  const nav = page.getByRole("navigation", { name: "Navegación principal" });
  const dialog = page.getByRole("dialog");
  const checkA11y = async () => {
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(result.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) }))).toEqual([]);
  };
  await checkA11y();
  await nav.getByRole("button", { name: "Contactos", exact: true }).click();
  await page.getByRole("button", { name: /Contacto prueba/ }).click();
  await checkA11y();
  await dialog.getByRole("button", { name: "Editar contacto", exact: true }).click();
  await dialog.getByLabel("Nombre", { exact: true }).fill("Contacto editado");
  await dialog.getByLabel("Notas").fill("<script>alert('texto')</script>");
  await dialog.getByRole("button", { name: "Guardar contacto" }).click();
  await expect(dialog.getByRole("heading", { name: "Contacto editado" })).toBeVisible();
  await dialog.getByRole("button", { name: "Archivar contacto", exact: true }).click();
  await expect(dialog).toContainText("1 pendientes activos");
  await dialog.getByRole("button", { name: "Confirmar archivo" }).click();
  await expect(dialog.getByText("Contacto archivado", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Archivados", exact: true }).click();
  await page.getByRole("button", { name: /Contacto editado/ }).click();
  await dialog.getByRole("button", { name: "Restaurar contacto", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirmar restauración" }).click();
  await expect(dialog.getByText("Contacto activo", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await nav.getByRole("button", { name: "Resumen", exact: true }).click();
  const row = page.getByRole("button", { name: /Contacto editado/ });
  await row.click();
  await dialog.getByRole("button", { name: "Editar pendiente", exact: true }).click();
  await dialog.getByLabel("Concepto", { exact: true }).fill("Concepto corregido");
  await dialog.getByLabel("Notas", { exact: true }).fill("Notas conservadas");
  const close = dialog.getByRole("button", { name: "Cerrar", exact: true });
  const save = dialog.getByRole("button", { name: "Guardar cambios" });
  await close.focus();
  await page.keyboard.press("Shift+Tab");
  await expect(save).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await checkA11y();
  await dialog.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(dialog).toContainText("Concepto corregido");
  await dialog.getByRole("button", { name: "Cancelar pendiente", exact: true }).click();
  await dialog.getByRole("button", { name: "Confirmar cancelación" }).click();
  await expect(dialog).toContainText("Cancelado. El saldo se conserva");
  await expect(dialog.locator(".balance-callout")).toContainText("$10,000.00");
  await page.keyboard.press("Escape");
  await expect(row).toBeFocused();
  await expect(page.locator(".hero-stat")).toContainText("$0.00");
  await checkA11y();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar mis datos" }).click();
  const download = await downloadPromise;
  const exported = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(exported.contacts[0].name).toBe("Contacto editado");
  expect(exported.commitments[0].lifecycle_status).toBe("cancelled");
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `.local/nomi-completed-${info.project.name}.png`, fullPage: true });
});

test("almacenamiento bloqueado o lleno no envía pagos", async ({ page }) => {
  await account(page, "storage");
  const { commitment } = await seed(page);
  await openPayment(page);
  let payments = 0;
  page.on("request", request => { if (request.method() === "POST" && request.url().endsWith("/transactions")) payments++; });
  await page.evaluate(() => { Object.defineProperty(indexedDB, "open", { configurable: true, value: () => { throw new DOMException("blocked", "SecurityError"); } }); });
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar abono" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("bloqueó el almacenamiento");
  expect(payments).toBe(0);
  await page.reload();
  await openPayment(page);
  await page.evaluate(() => { IDBObjectStore.prototype.add = function () { throw new DOMException("Sin espacio para conservar la operación", "QuotaExceededError"); }; });
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar abono" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  expect(payments).toBe(0);
  expect((await (await page.request.get(`/api/v1/commitments/${commitment.id}/transactions`)).json()).items).toHaveLength(0);
});

test("sesión vencida y desconexión conservan la intención", async ({ page, context }) => {
  const credentials = await account(page, "expired");
  const { commitment, headers } = await seed(page);
  await openPayment(page);
  expect((await page.request.post("/api/v1/auth/logout", { headers, data: {} })).status()).toBe(204);
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar abono" }).click();
  await expect(page.getByRole("heading", { name: "Empieza con claridad." })).toBeVisible();
  expect((await page.request.post("/api/v1/auth/login", { headers: { Origin: "http://localhost:3000" }, data: credentials })).status()).toBe(200);
  await page.reload();
  await expect(page.getByRole("button", { name: "Revisar operación pendiente" })).toBeVisible();
  await context.setOffline(true);
  await expect(page.getByRole("status").filter({ hasText: "Sin conexión" })).toBeVisible();
  await page.getByRole("button", { name: "Revisar operación pendiente" }).click();
  await expect(page.getByRole("complementary", { name: "Operación pendiente" })).toContainText("No pudimos confirmar");
  await context.setOffline(false);
  await page.getByRole("button", { name: "Revisar operación pendiente" }).click();
  await expect(page.getByRole("complementary", { name: "Operación pendiente" })).toBeHidden();
  await expect(page.locator(".hero-stat")).toContainText("$7,500.00");
  expect((await (await page.request.get(`/api/v1/commitments/${commitment.id}/transactions`)).json()).items).toHaveLength(1);
});

test("dos pestañas no confirman intenciones financieras simultáneas", async ({ page, context }) => {
  await account(page, "tabs");
  const { commitment } = await seed(page);
  const other = await context.newPage();
  await other.goto("/");
  await openPayment(page);
  await openPayment(other);
  let release!: () => void;
  let entered!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  const started = new Promise<void>(resolve => { entered = resolve; });
  await page.route("**/api/v1/commitments/*/transactions", async route => {
    if (route.request().method() !== "POST") return route.continue();
    entered(); await held; await route.continue();
  });
  try {
    await page.getByRole("dialog").getByRole("button", { name: "Confirmar abono" }).click();
    await started;
    await other.getByRole("dialog").getByRole("button", { name: "Confirmar abono" }).click();
    await expect(other.getByRole("dialog").getByRole("alert")).toContainText("otra pestaña");
  } finally { release(); }
  await expect(page.getByRole("dialog").locator(".balance-callout")).toContainText("$7,500.00");
  expect((await (await page.request.get(`/api/v1/commitments/${commitment.id}/transactions`)).json()).items).toHaveLength(1);
  await other.close();
});
