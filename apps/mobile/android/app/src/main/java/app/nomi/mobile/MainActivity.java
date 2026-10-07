package app.nomi.mobile;

import com.getcapacitor.BridgeActivity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.CookieManager;
import java.net.CookieHandler;

public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle savedInstanceState) {
        registerPlugin(NomiApiPlugin.class);
        super.onCreate(savedInstanceState);
        // Capacitor installs a global cookie handler even with its JS cookie plugin disabled.
        // Nomi owns HTTP credentials exclusively in SessionVault, never in WebView storage.
        CookieHandler.setDefault(null);
        CookieManager.getInstance().setAcceptCookie(false);
        CookieManager.getInstance().removeAllCookies(null);
        CookieManager.getInstance().flush();
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
    }
}
