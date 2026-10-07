package app.nomi.mobile;

import java.net.URI;

final class RequestPolicy {
    static URI destination(String base, String path, String method, boolean debug) {
        if (!path.matches("^/[a-zA-Z0-9/_-]+(?:\\?[^#\\r\\n]*)?$") || path.startsWith("//") ||
            !(method.equals("GET") || method.equals("POST") || method.equals("PATCH"))) throw new IllegalArgumentException();
        URI origin = URI.create(base);
        if (origin.getHost() == null || origin.getUserInfo() != null || origin.getQuery() != null || origin.getFragment() != null ||
            !(origin.getPath().isEmpty() || origin.getPath().equals("/"))) throw new IllegalArgumentException();
        if (!("https".equals(origin.getScheme()) || (debug && "http".equals(origin.getScheme()) &&
            (origin.getHost().equals("127.0.0.1") || origin.getHost().equals("localhost"))))) throw new IllegalArgumentException();
        return URI.create(base.replaceAll("/$", "") + "/api/v1" + path);
    }
}
