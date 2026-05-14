/*
 * HTTP API bridge for the custom messenger server.
 *
 * Provides static helper methods that translate Telegram-style API calls
 * into HTTP requests against the Python server.  The Android client can
 * call these methods instead of (or in addition to) the native MTProto
 * layer when {@link CustomServerConfig#USE_CUSTOM_SERVER} is enabled.
 *
 * All networking runs on background threads; results are delivered on
 * the main/UI thread via the supplied callbacks.
 */
package org.telegram.messenger;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class CustomApiClient {

    public interface ApiCallback {
        void onSuccess(JSONObject response);
        void onError(int code, String message);
    }

    private static final ExecutorService executor = Executors.newFixedThreadPool(4);
    private static final Handler mainHandler = new Handler(Looper.getMainLooper());

    // ── Generic POST ────────────────────────────────────────────────────

    public static void post(String path, JSONObject body, ApiCallback callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(CustomServerConfig.apiUrl(path));
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                if (CustomServerConfig.AUTH_TOKEN != null) {
                    conn.setRequestProperty("Authorization", "Bearer " + CustomServerConfig.AUTH_TOKEN);
                }
                conn.setDoOutput(true);
                conn.setConnectTimeout(15_000);
                conn.setReadTimeout(30_000);

                byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
                try (DataOutputStream os = new DataOutputStream(conn.getOutputStream())) {
                    os.write(data);
                }

                int status = conn.getResponseCode();
                BufferedReader reader;
                if (status >= 200 && status < 300) {
                    reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8));
                } else {
                    reader = new BufferedReader(new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8));
                }
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                reader.close();

                JSONObject json = new JSONObject(sb.toString());
                if (status >= 200 && status < 300) {
                    mainHandler.post(() -> callback.onSuccess(json));
                } else {
                    String detail = json.optString("detail", "Unknown error");
                    mainHandler.post(() -> callback.onError(status, detail));
                }
            } catch (Exception e) {
                mainHandler.post(() -> callback.onError(-1, e.getMessage()));
            }
        });
    }

    // ── Auth ─────────────────────────────────────────────────────────────

    public static void sendCode(String phone, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("phone", phone);
            post("/api/auth/sendCode", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void signIn(String phone, String phoneCodeHash, String code, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("phone", phone);
            body.put("phone_code_hash", phoneCodeHash);
            body.put("code", code);
            post("/api/auth/signIn", body, new ApiCallback() {
                @Override
                public void onSuccess(JSONObject response) {
                    CustomServerConfig.AUTH_TOKEN = response.optString("auth_token", null);
                    callback.onSuccess(response);
                }

                @Override
                public void onError(int errCode, String message) {
                    callback.onError(errCode, message);
                }
            });
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void signUp(String phone, String phoneCodeHash, String code,
                               String firstName, String lastName, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("phone", phone);
            body.put("phone_code_hash", phoneCodeHash);
            body.put("code", code);
            body.put("first_name", firstName);
            body.put("last_name", lastName);
            post("/api/auth/signUp", body, new ApiCallback() {
                @Override
                public void onSuccess(JSONObject response) {
                    CustomServerConfig.AUTH_TOKEN = response.optString("auth_token", null);
                    callback.onSuccess(response);
                }

                @Override
                public void onError(int errCode, String message) {
                    callback.onError(errCode, message);
                }
            });
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Messages ─────────────────────────────────────────────────────────

    public static void sendMessage(long chatId, String text, Long replyToMsgId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("text", text);
            if (replyToMsgId != null) {
                body.put("reply_to_msg_id", replyToMsgId);
            }
            post("/api/messages/sendMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getHistory(long chatId, long offsetId, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("offset_id", offsetId);
            body.put("limit", limit);
            post("/api/messages/getHistory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getDialogs(int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/messages/getDialogs", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Contacts ─────────────────────────────────────────────────────────

    public static void getContacts(ApiCallback callback) {
        post("/api/contacts/getContacts", new JSONObject(), callback);
    }

    public static void searchContacts(String query, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("query", query);
            body.put("limit", limit);
            post("/api/contacts/search", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Chats ────────────────────────────────────────────────────────────

    public static void createChat(String title, long[] userIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("title", title);
            JSONArray ids = new JSONArray();
            for (long id : userIds) {
                ids.put(id);
            }
            body.put("user_ids", ids);
            post("/api/chats/createChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void startPrivateChat(long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            post("/api/chats/startPrivate", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Users ────────────────────────────────────────────────────────────

    public static void getMe(ApiCallback callback) {
        post("/api/users/getMe", new JSONObject(), callback);
    }

    public static void updateProfile(String firstName, String lastName, String bio, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            if (firstName != null) body.put("first_name", firstName);
            if (lastName != null) body.put("last_name", lastName);
            if (bio != null) body.put("bio", bio);
            post("/api/users/updateProfile", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }
}
