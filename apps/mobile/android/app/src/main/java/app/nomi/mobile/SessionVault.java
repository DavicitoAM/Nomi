package app.nomi.mobile;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import org.json.JSONObject;

/** No getters are exposed through the Capacitor bridge. Called on one native executor. */
final class SessionVault {
    private final Context context;
    private static final String ALIAS = "nomi.session.v1";
    SessionVault(Context context) { this.context = context; }

    private SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return generator.generateKey();
    }
    private byte[] associatedData() { return (BuildConfig.API_URL + "|" + BuildConfig.WEB_ORIGIN).getBytes(StandardCharsets.UTF_8); }
    JSONObject read() throws Exception {
        String sealed = context.getSharedPreferences("nomi-vault", Context.MODE_PRIVATE).getString("sealed", null);
        if (sealed == null) return new JSONObject();
        try {
            JSONObject envelope = new JSONObject(sealed);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, Base64.decode(envelope.getString("iv"), Base64.NO_WRAP)));
            cipher.updateAAD(associatedData());
            return new JSONObject(new String(cipher.doFinal(Base64.decode(envelope.getString("data"), Base64.NO_WRAP)), StandardCharsets.UTF_8));
        } catch (Exception invalidated) {
            // Lost/invalidated key requires login; pending financial intents remain untouched.
            clear();
            return new JSONObject();
        }
    }
    void write(JSONObject value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        cipher.updateAAD(associatedData());
        JSONObject envelope = new JSONObject()
            .put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
            .put("data", Base64.encodeToString(cipher.doFinal(value.toString().getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP));
        if (!context.getSharedPreferences("nomi-vault", Context.MODE_PRIVATE).edit().putString("sealed", envelope.toString()).commit())
            throw new IllegalStateException("Session storage unavailable");
    }
    void clear() {
        if (!context.getSharedPreferences("nomi-vault", Context.MODE_PRIVATE).edit().clear().commit())
            throw new IllegalStateException("Session storage unavailable");
    }
}
