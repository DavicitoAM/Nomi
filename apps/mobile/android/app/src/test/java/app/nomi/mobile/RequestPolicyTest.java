package app.nomi.mobile;

import org.junit.Test;
import static org.junit.Assert.*;

public class RequestPolicyTest {
    @Test public void releaseUsesFixedHttpsOrigin() {
        assertEquals("https://api.example.com/api/v1/contacts?search=Juan",
            RequestPolicy.destination("https://api.example.com", "/contacts?search=Juan", "GET", false).toString());
    }
    @Test public void blocksCredentialRedirectionAndTraversal() {
        for (String path : new String[]{"https://evil.example/me", "//evil.example/me", "/../me", "/%2e%2e/me", "/me#fragment", "/me\r\nX: bad"})
            assertThrows(IllegalArgumentException.class, () -> RequestPolicy.destination("https://api.example.com", path, "GET", false));
    }
    @Test public void debugHttpIsLoopbackOnly() {
        assertEquals("127.0.0.1", RequestPolicy.destination("http://127.0.0.1:8000", "/me", "GET", true).getHost());
        assertThrows(IllegalArgumentException.class, () -> RequestPolicy.destination("http://192.168.1.10", "/me", "GET", true));
        assertThrows(IllegalArgumentException.class, () -> RequestPolicy.destination("http://127.0.0.1", "/me", "GET", false));
    }
    @Test public void disallowsOriginsWithCredentialsAndUnapprovedMethods() {
        // Userinfo below is synthetic invalid input, never an application credential.
        for (String origin : new String[]{"https://user:secret@api.example.com", "https://api.example.com/nested", "https://api.example.com?override=1", "file:///tmp"}) // pragma: allowlist secret
            assertThrows(IllegalArgumentException.class, () -> RequestPolicy.destination(origin, "/me", "GET", false));
        assertThrows(IllegalArgumentException.class, () -> RequestPolicy.destination("https://api.example.com", "/me", "DELETE", false));
    }
}
