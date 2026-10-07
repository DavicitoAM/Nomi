import { Capacitor, registerPlugin } from "@capacitor/core";
import { App } from "@capacitor/app";
import { focusManager } from "@tanstack/react-query";
import { platform, type ApiRequest } from "@/lib/platform";

interface NativeApi {
  request(input: ApiRequest): Promise<{ status: number; body: string }>;
  saveExport(input: { data: string }): Promise<void>;
}
const native = registerPlugin<NativeApi>("NomiApi");

// Only this app's explicit account-link scheme. Tokens stay in memory and are consumed by Core.
export function accountFragment(url: string): string | null {
  try {
    const value = new URL(url);
    if (value.protocol !== "nomi:" || value.hostname !== "account" || value.pathname !== "") return null;
    const fields = new URLSearchParams(value.hash.slice(1));
    const action = fields.get("action"), token = fields.get("token");
    if (!["verify", "reset"].includes(action ?? "") || !token || !/^[A-Za-z0-9_-]{20,256}$/.test(token)) return null;
    return new URLSearchParams({ action: action!, token }).toString();
  } catch { return null; }
}

export function setupAndroid() {
  if (Capacitor.getPlatform() !== "android") return;
  platform.request = async request => {
    const result = await native.request(request);
    return new Response(result.status === 204 ? null : result.body, { status: result.status, headers: { "Content-Type": "application/json" } });
  };
  platform.saveExport = async data => { await native.saveExport({ data: JSON.stringify(data) }); };
  const openLink = (url: string) => { const fragment = accountFragment(url); if (fragment) window.location.hash = fragment; };
  void App.addListener("appUrlOpen", event => openLink(event.url));
  void App.getLaunchUrl().then(event => { if (event) openLink(event.url); });
  void App.addListener("backButton", () => {
    const dialog = document.querySelector<HTMLDialogElement>("dialog[open]");
    if (dialog) dialog.dispatchEvent(new Event("cancel", { cancelable: true }));
    else void App.minimizeApp();
  });
  void App.addListener("appStateChange", event => {
    focusManager.setFocused(event.isActive);
    if (event.isActive) window.dispatchEvent(new Event("focus"));
  });
}
