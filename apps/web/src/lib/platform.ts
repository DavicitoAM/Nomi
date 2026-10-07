// Platform capabilities are installed at startup by the Android entry point only.
export type ApiRequest = { path: string; method: string; body?: string; key?: string };
export type ApiTransport = (request: ApiRequest) => Promise<Response>;
export const platform: { request?: ApiTransport; saveExport?: (data: object) => Promise<void> } = {};
