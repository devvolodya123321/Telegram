/*
 * Custom Messenger Server configuration.
 *
 * When USE_CUSTOM_SERVER is true the client will route its API calls
 * through the Python server instead of Telegram's MTProto datacenters.
 *
 * Set CUSTOM_SERVER_URL to the base URL of your deployed server
 * (for example "https://my-messenger.example.com" or
 * "http://192.168.1.100:8443" for local development).
 */
package org.telegram.messenger;

public class CustomServerConfig {

    /**
     * Master switch: set to {@code true} to redirect all API traffic
     * to the custom Python server defined by {@link #CUSTOM_SERVER_URL}.
     */
    public static boolean USE_CUSTOM_SERVER = false;

    /**
     * Base URL of the custom messenger server (no trailing slash).
     * Examples:
     *   "http://10.0.2.2:8443"          — Android emulator → host machine
     *   "http://192.168.1.100:8443"      — physical device on the same LAN
     *   "https://messenger.example.com"  — production deployment
     */
    public static String CUSTOM_SERVER_URL = "http://10.0.2.2:8443";

    /**
     * WebSocket URL for real-time updates.
     * Derived automatically from {@link #CUSTOM_SERVER_URL} but can
     * be overridden if the WS endpoint is hosted separately.
     */
    public static String getWebSocketUrl() {
        String base = CUSTOM_SERVER_URL;
        if (base.startsWith("https://")) {
            return "wss://" + base.substring(8) + "/api/updates/ws";
        }
        return "ws://" + base.substring(7) + "/api/updates/ws";
    }

    /**
     * Auth token stored after successful sign-in / sign-up.
     * Sent as {@code Authorization: Bearer <token>} on every request.
     */
    public static String AUTH_TOKEN = null;

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
