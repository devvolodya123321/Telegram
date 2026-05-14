/*
 * Custom Messenger Server configuration.
 *
 * The client routes ALL API calls through the custom Python server.
 * Telegram's MTProto datacenters are not used at all.
 * No API ID or API hash is required — authentication is handled
 * entirely by the custom server.
 */
package org.telegram.messenger;

public class CustomServerConfig {

    /**
     * Master switch — always enabled for our custom messenger.
     */
    public static boolean USE_CUSTOM_SERVER = true;

    /**
     * Base URL of the custom messenger server (no trailing slash).
     */
    public static String CUSTOM_SERVER_URL = "http://45.90.99.234:8443";

    /**
     * WebSocket URL for real-time updates.
     */
    public static String getWebSocketUrl() {
        String base = CUSTOM_SERVER_URL;
        if (base.startsWith("https://")) {
            return "wss://" + base.substring(8) + "/ws/updates";
        }
        return "ws://" + base.substring(7) + "/ws/updates";
    }

    /**
     * Auth token stored after successful sign-in / sign-up.
     * Sent as {@code Authorization: Bearer <token>} on every request.
     */
    public static String AUTH_TOKEN = null;

    /**
     * The verification code is always "22222" on our server.
     * The client can auto-fill or display this to the user.
     */
    public static final String DEFAULT_CODE = "22222";

    /**
     * Convenience: full API URL for a given endpoint path.
     *
     * @param path e.g. "/api/auth/sendCode"
     * @return full URL
     */
    public static String apiUrl(String path) {
        return CUSTOM_SERVER_URL + path;
    }
}
