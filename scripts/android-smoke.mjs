// Real Android WebView + native Keystore/HTTP bridge. Synthetic data, emulator only.
import { _android, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const adbPath = process.env.ANDROID_HOME ? path.join(process.env.ANDROID_HOME, 'platform-tools', 'adb.exe') : path.join(root, '.local/android-sdk/platform-tools/adb.exe');
const serial = process.env.NOMI_EMULATOR ?? 'emulator-5554';
if (!serial.startsWith('emulator-')) throw new Error('This smoke test is restricted to a synthetic emulator.');
const app = 'app.nomi.mobile.debug';
const adb = (...args) => execFileSync(adbPath, ['-s', serial, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const report = { scope: 'android-emulator', checks: [] };
const check = label => { report.checks.push(label); console.log(label); };
let device;

async function connect() {
  device = (await _android.devices()).find(candidate => candidate.serial() === serial);
  if (!device) throw new Error('Synthetic Android emulator is not available');
  const view = await device.webView({ pkg: app }, { timeout: 45000 });
  const page = await view.page();
  page.setDefaultTimeout(15000);
  return page;
}
async function restart() {
  adb('shell', 'am', 'force-stop', 'com.microsoft.playwright.androiddriver');
  if (device) await device.close();
  adb('shell', 'am', 'force-stop', app);
  adb('shell', 'am', 'start', '-n', `${app}/app.nomi.mobile.MainActivity`);
  return connect();
}

try {
  await mkdir(path.join(root, '.local/android-evidence'), { recursive: true });
  adb('reverse', 'tcp:8000', 'tcp:8000');
  let page = await restart();
  const errors = [];
  page.on('pageerror', error => errors.push(error.name));
  await page.evaluate(async () => {
    await window.Capacitor.Plugins.NomiApi.request({ path: '/auth/logout', method: 'POST', body: '{}' });
  });
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Empieza con claridad.' })).toBeVisible();
  await page.getByLabel('Tu nombre').fill('Android');
  await page.getByLabel('Correo electrónico').fill(`android-${crypto.randomUUID()}@example.com`);
  await page.getByLabel('Contraseña', { exact: true }).fill(crypto.randomUUID() + 'Aa9!');
  await page.getByRole('button', { name: 'Crear mi espacio', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Hola, Android.' })).toBeVisible();
  check('register_and_native_session');
  expect(await page.evaluate(() => document.cookie.includes('nomi_'))).toBe(false);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  const sealed = adb('exec-out', 'run-as', app, 'cat', 'shared_prefs/nomi-vault.xml');
  expect(sealed).toContain('sealed');
  expect(sealed).not.toMatch(/nomi_session|nomi_csrf|@example.com/);
  check('credentials_hidden_from_javascript_and_encrypted_at_rest');
  await page.getByRole('button', { name: 'Registrar pendiente', exact: true }).first().click();
  let dialog = page.getByRole('dialog');
  await dialog.getByLabel('Nombre', { exact: true }).fill('Juan Android');
  await dialog.getByRole('button', { name: 'Guardar contacto' }).click();
  await dialog.getByLabel('Monto', { exact: false }).fill('10000');
  await dialog.getByLabel('Concepto', { exact: false }).fill('Prueba Android');
  await dialog.getByRole('button', { name: 'Guardar pendiente' }).click();
  await expect(dialog).toBeHidden();
  await expect(page.locator('.hero-stat')).toContainText('$10,000.00');
  check('contact_commitment_dashboard');
  await page.getByRole('button', { name: /Juan Android/ }).click();
  await dialog.getByRole('button', { name: 'Editar pendiente', exact: true }).click();
  await dialog.getByLabel('Concepto', { exact: true }).fill('Prueba Android actualizada');
  await dialog.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
  await expect(dialog).toContainText('Prueba Android actualizada');
  check('native_patch_descriptive_edit');
  await dialog.getByRole('button', { name: 'Registrar abono' }).click();
  await dialog.getByLabel('Monto del abono').fill('2500');
  await dialog.getByRole('button', { name: 'Confirmar abono' }).click();
  await expect(dialog.locator('.balance-callout')).toContainText('$7,500.00');
  check('payment_native_bridge_and_postgresql');
  adb('shell', 'input', 'keyevent', '4');
  await expect(dialog).toBeHidden();
  check('android_back_closes_dialog');
  page = await restart();
  await expect(page.getByRole('heading', { name: 'Hola, Android.' })).toBeVisible();
  await expect(page.locator('.hero-stat')).toContainText('$7,500.00');
  check('session_and_balance_survive_process_death');
  await page.getByRole('button', { name: /Juan Android/ }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByRole('button', { name: 'Revertir abono', exact: true }).click();
  await dialog.getByLabel('Motivo').fill('Prueba de reversión Android');
  await dialog.getByRole('button', { name: 'Confirmar reversión', exact: true }).click();
  await expect(dialog.locator('.balance-callout')).toContainText('$10,000.00');
  await expect(dialog.getByText('Abono revertido', { exact: true })).toBeVisible();
  await expect(dialog.getByText('Reversión registrada', { exact: true })).toBeVisible();
  check('reversal_and_linked_history');
  await dialog.getByRole('button', { name: 'Registrar abono', exact: true }).click();
  await dialog.getByLabel('Monto del abono').fill('100');
  adb('reverse', '--remove', 'tcp:8000');
  // Let Uvicorn's existing keep-alive connection expire; removing an ADB mapping alone
  // does not close streams that have already connected through it.
  await new Promise(resolve => setTimeout(resolve, 7000));
  await dialog.getByRole('button', { name: 'Confirmar abono', exact: true }).click();
  await expect(dialog.getByRole('alert')).toBeVisible({ timeout: 25000 });
  const pendingKeys = () => page.evaluate(() => new Promise((resolve, reject) => {
    const request = indexedDB.open('nomi-financial-intents', 1);
    request.onerror = () => reject(new Error('IndexedDB unavailable'));
    request.onsuccess = () => {
      const db = request.result;
      const read = db.transaction('pending').objectStore('pending').getAll();
      read.onsuccess = () => { resolve(read.result.map(row => row.key)); db.close(); };
    };
  }));
  const keys = await pendingKeys();
  expect(keys).toHaveLength(1);
  adb('reverse', 'tcp:8000', 'tcp:8000');
  page = await restart();
  await expect(page.getByRole('heading', { name: 'Hola, Android.' })).toBeVisible();
  expect(await pendingKeys()).toEqual(keys);
  await page.getByRole('button', { name: 'Revisar operación pendiente', exact: true }).click();
  await expect(page.locator('.hero-stat')).toContainText('$9,900.00');
  await expect(page.getByRole('button', { name: 'Revisar operación pendiente', exact: true })).toBeHidden();
  expect(await pendingKeys()).toEqual([]);
  await page.getByRole('button', { name: /Juan Android/ }).click();
  dialog = page.getByRole('dialog');
  await expect(dialog.getByText('Abono registrado', { exact: true })).toHaveCount(1);
  check('network_failure_durable_intent_restart_and_single_recovery');
  await dialog.getByRole('button', { name: 'Cerrar', exact: true }).click();
  const rejected = await page.evaluate(async () => {
    try { await window.Capacitor.Plugins.NomiApi.request({ path: '//other.example/me', method: 'GET' }); return false; }
    catch { return true; }
  });
  expect(rejected).toBe(true);
  check('native_transport_rejects_foreign_destination');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await writeFile(path.join(root, '.local/android-evidence/dashboard.png'), execFileSync(adbPath, ['-s', serial, 'exec-out', 'screencap', '-p']));
  await page.getByRole('button', { name: 'Exportar mis datos', exact: true }).click();
  const exportName = `nomi-smoke-${crypto.randomUUID()}.json`;
  await device.fill({ res: 'android:id/title', clazz: 'android.widget.EditText' }, exportName);
  await device.tap({ res: 'android:id/button1' });
  await expect(page.getByRole('button', { name: 'Exportar mis datos', exact: true })).toBeEnabled();
  const exported = JSON.parse(adb('shell', 'cat', `/sdcard/Download/${exportName}`));
  expect(exported.contacts[0].name).toBe('Juan Android');
  expect(exported.commitments[0].balance_minor).toBe(990000);
  expect(exported.transactions).toHaveLength(3);
  check('native_file_picker_exports_consistent_json');
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Empieza con claridad.' })).toBeVisible();
  page = await restart();
  await expect(page.getByRole('heading', { name: 'Empieza con claridad.' })).toBeVisible();
  check('logout_survives_process_restart');
  expect(errors).toEqual([]);
  report.status = 'passed';
} catch (error) {
  report.status = 'failed';
  report.error = error.name;
  console.error(error.message);
  process.exitCode = 1;
} finally {
  adb('reverse', 'tcp:8000', 'tcp:8000');
  adb('shell', 'am', 'force-stop', 'com.microsoft.playwright.androiddriver');
  if (device) await device.close();
  await writeFile(path.join(root, '.local/android-evidence/report.json'), JSON.stringify(report, null, 2));
}
