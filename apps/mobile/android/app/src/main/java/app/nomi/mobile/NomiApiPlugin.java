package app.nomi.mobile;

import android.app.Activity;
import android.content.Intent;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.ActivityCallback;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.net.HttpCookie;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

@CapacitorPlugin(name = "NomiApi")
public class NomiApiPlugin extends Plugin {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private SessionVault vault;
    @Override public void load() { vault = new SessionVault(getContext()); }
    @Override protected void handleOnDestroy() { executor.shutdown(); }

    @PluginMethod public void request(PluginCall call) {
        executor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                String path = call.getString("path", "");
                String method = call.getString("method", "GET");
                URI destination = RequestPolicy.destination(BuildConfig.API_URL, path, method, BuildConfig.DEBUG);
                String body = call.getString("body");
                byte[] bytes = body == null ? new byte[0] : body.getBytes(StandardCharsets.UTF_8);
                if (bytes.length > 16384 || (method.equals("GET") && bytes.length > 0)) throw new IllegalArgumentException();
                String key = call.getString("key");
                if (key != null) UUID.fromString(key);
                JSONObject session = vault.read();
                if (session.optLong("expires", 0) < System.currentTimeMillis()) { vault.clear(); session = new JSONObject(); }
                connection = (HttpURLConnection) destination.toURL().openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(15000); connection.setReadTimeout(15000);
                connection.setInstanceFollowRedirects(false); connection.setUseCaches(false);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setRequestProperty("Origin", BuildConfig.WEB_ORIGIN);
                if (session.has("session")) connection.setRequestProperty("Cookie", "nomi_session=" + session.getString("session"));
                if (session.has("csrf")) connection.setRequestProperty("X-CSRF-Token", session.getString("csrf"));
                if (key != null) connection.setRequestProperty("Idempotency-Key", key);
                if (body != null) {
                    connection.setDoOutput(true); connection.setFixedLengthStreamingMode(bytes.length);
                    try (OutputStream output = connection.getOutputStream()) { output.write(bytes); }
                }
                int status = connection.getResponseCode();
                if (status >= 300 && status < 400) throw new IllegalStateException("Redirect rejected");
                boolean changed = false;
                for (Map.Entry<String,List<String>> entry : connection.getHeaderFields().entrySet()) {
                    if (entry.getKey() == null || !entry.getKey().equalsIgnoreCase("Set-Cookie")) continue;
                    for (String header : entry.getValue()) for (HttpCookie cookie : HttpCookie.parse(header)) {
                        String field = cookie.getName().equals("nomi_session") ? "session" : cookie.getName().equals("nomi_csrf") ? "csrf" : null;
                        if (field == null) continue;
                        changed = true;
                        if (cookie.getMaxAge() == 0 || cookie.getValue().isEmpty()) session.remove(field);
                        else {
                            session.put(field, cookie.getValue());
                            if (field.equals("session")) session.put("expires", System.currentTimeMillis() + Math.max(0, cookie.getMaxAge()) * 1000);
                        }
                    }
                }
                if (changed) { if (session.has("session")) vault.write(session); else vault.clear(); }
                if (status == 401 && !path.startsWith("/auth/")) vault.clear();
                String text = "";
                InputStream input = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
                if (input != null) try (input; ByteArrayOutputStream result = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[8192]; int count;
                    while ((count = input.read(buffer)) != -1) {
                        if (result.size() + count > 11 * 1024 * 1024) throw new IllegalStateException("Response too large");
                        result.write(buffer, 0, count);
                    }
                    text = result.toString(StandardCharsets.UTF_8.name());
                }
                call.resolve(new JSObject().put("status", status).put("body", text));
            } catch (Exception error) {
                // Never log exceptions, requests, cookies, tokens or response bodies.
                call.reject("No se pudo confirmar la respuesta del servidor.", "NATIVE_REQUEST_FAILED");
            } finally { if (connection != null) connection.disconnect(); }
        });
    }

    @PluginMethod public void saveExport(PluginCall call) {
        String data = call.getString("data", "");
        if (data.getBytes(StandardCharsets.UTF_8).length > 11 * 1024 * 1024) { call.reject("Archivo demasiado grande."); return; }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
            .setType("application/json").putExtra(Intent.EXTRA_TITLE, "nomi-workspace.json");
        startActivityForResult(call, intent, "exportSelected");
    }
    @ActivityCallback private void exportSelected(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) { call.resolve(); return; }
        try (OutputStream output = getContext().getContentResolver().openOutputStream(result.getData().getData(), "wt")) {
            if (output == null) throw new IllegalStateException();
            output.write(call.getString("data", "").getBytes(StandardCharsets.UTF_8));
            call.resolve();
        } catch (Exception error) { call.reject("No se pudo guardar el archivo."); }
    }
}
