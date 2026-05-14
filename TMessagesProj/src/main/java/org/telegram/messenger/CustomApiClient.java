/*
 * HTTP API bridge for the custom messenger server.
 *
 * Provides static helper methods that translate Telegram-style API calls
 * into HTTP requests against the Python server.  No Telegram API ID or
 * API hash is needed — the custom server handles everything.
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

    public static void logOut(ApiCallback callback) {
        post("/api/auth/logOut", new JSONObject(), callback);
    }

    public static void setPassword(String password, String hint, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("password", password);
            if (hint != null) body.put("hint", hint);
            post("/api/auth/setPassword", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void checkPassword(String password, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("password", password);
            post("/api/auth/checkPassword", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteAccount(String reason, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            if (reason != null) body.put("reason", reason);
            post("/api/auth/deleteAccount", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getPasswordHint(ApiCallback callback) {
        post("/api/auth/getPasswordHint", new JSONObject(), callback);
    }

    public static void resetPassword(ApiCallback callback) {
        post("/api/auth/resetPassword", new JSONObject(), callback);
    }

    // ── Users / Profile ─────────────────────────────────────────────────

    public static void getMe(ApiCallback callback) {
        post("/api/users/getMe", new JSONObject(), callback);
    }

    public static void getUser(long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            post("/api/users/getUser", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getUsers(long[] userIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            JSONArray ids = new JSONArray();
            for (long id : userIds) ids.put(id);
            body.put("user_ids", ids);
            post("/api/users/getUsers", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
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

    public static void updateUsername(String username, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("username", username);
            post("/api/users/updateUsername", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void setPrivacy(String key, String value, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put(key, value);
            post("/api/users/setPrivacy", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getPrivacy(ApiCallback callback) {
        post("/api/users/getPrivacy", new JSONObject(), callback);
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

    public static void blockUser(long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            post("/api/contacts/block", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void unblockUser(long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            post("/api/contacts/unblock", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getBlocked(int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/contacts/getBlocked", body, callback);
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
            for (long id : userIds) ids.put(id);
            body.put("user_ids", ids);
            post("/api/chats/createChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void createChannel(String title, String description, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("title", title);
            if (description != null) body.put("description", description);
            post("/api/chats/createChannel", body, callback);
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

    public static void editChatTitle(long chatId, String title, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("title", title);
            post("/api/chats/editTitle", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void editChatDescription(long chatId, String description, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("description", description);
            post("/api/chats/editDescription", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void addUserToChat(long chatId, long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("user_id", userId);
            post("/api/chats/addUser", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteUserFromChat(long chatId, long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("user_id", userId);
            post("/api/chats/deleteUser", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getFullChat(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/chats/getFullChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getMembers(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/chats/getMembers", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void leaveChat(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/chats/leaveChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void joinChat(String username, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("username", username);
            post("/api/chats/joinChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void pinMessage(long chatId, long messageId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("message_id", messageId);
            post("/api/chats/pinMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void unpinMessage(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/chats/unpinMessage", body, callback);
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
            if (replyToMsgId != null) body.put("reply_to_msg_id", replyToMsgId);
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

    public static void readHistory(long chatId, long maxId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("max_id", maxId);
            post("/api/messages/readHistory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteMessages(long chatId, long[] messageIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            JSONArray ids = new JSONArray();
            for (long id : messageIds) ids.put(id);
            body.put("message_ids", ids);
            post("/api/messages/deleteMessages", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void editMessage(long chatId, long messageId, String text, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("message_id", messageId);
            body.put("text", text);
            post("/api/messages/editMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void forwardMessages(long fromChatId, long toChatId, long[] messageIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("from_chat_id", fromChatId);
            body.put("to_chat_id", toChatId);
            JSONArray ids = new JSONArray();
            for (long id : messageIds) ids.put(id);
            body.put("message_ids", ids);
            post("/api/messages/forwardMessages", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void searchMessages(Long chatId, String query, int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            if (chatId != null) body.put("chat_id", chatId);
            body.put("query", query);
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/messages/search", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getPinnedMessages(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/messages/getPinnedMessages", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Calls ────────────────────────────────────────────────────────────

    public static void requestCall(long userId, String callType, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            body.put("call_type", callType);
            post("/api/calls/requestCall", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void acceptCall(long callId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("call_id", callId);
            post("/api/calls/acceptCall", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void discardCall(long callId, String reason, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("call_id", callId);
            body.put("reason", reason);
            post("/api/calls/discardCall", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void setCallRating(long callId, int rating, String comment, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("call_id", callId);
            body.put("rating", rating);
            if (comment != null) body.put("comment", comment);
            post("/api/calls/setCallRating", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getCallHistory(int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/calls/getCallHistory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Stickers ─────────────────────────────────────────────────────────

    public static void getStickerSets(ApiCallback callback) {
        post("/api/stickers/getStickerSets", new JSONObject(), callback);
    }

    public static void createStickerSet(String name, String title, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("name", name);
            body.put("title", title);
            post("/api/stickers/createStickerSet", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void removeStickerSet(long setId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("set_id", setId);
            post("/api/stickers/removeStickerSet", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void sendSticker(long chatId, long stickerId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("sticker_id", stickerId);
            post("/api/stickers/sendSticker", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Reactions ────────────────────────────────────────────────────────

    public static void sendReaction(long chatId, long messageId, String emoji, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("message_id", messageId);
            body.put("emoji", emoji);
            post("/api/reactions/sendReaction", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getReactions(long chatId, long messageId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("message_id", messageId);
            post("/api/reactions/getReactions", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Stories ──────────────────────────────────────────────────────────

    public static void getStories(long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("user_id", userId);
            post("/api/stories/getStories", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteStory(long storyId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("story_id", storyId);
            post("/api/stories/deleteStory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void viewStory(long storyId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("story_id", storyId);
            post("/api/stories/viewStory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Notifications ───────────────────────────────────────────────────

    public static void setNotificationSettings(Long chatId, Boolean muted, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            if (chatId != null) body.put("chat_id", chatId);
            if (muted != null) body.put("muted", muted);
            post("/api/notifications/setNotificationSettings", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getNotificationSettings(Long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            if (chatId != null) body.put("chat_id", chatId);
            post("/api/notifications/getNotificationSettings", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void muteChat(long chatId, long muteUntil, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("mute_until", muteUntil);
            post("/api/notifications/muteChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void unmuteChat(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/notifications/unmuteChat", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Polls ────────────────────────────────────────────────────────────

    public static void createPoll(long chatId, String question, String[] options, boolean isAnonymous, boolean multipleChoice, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("question", question);
            JSONArray opts = new JSONArray();
            for (String o : options) opts.put(o);
            body.put("options", opts);
            body.put("is_anonymous", isAnonymous);
            body.put("multiple_choice", multipleChoice);
            post("/api/polls/createPoll", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void votePoll(long pollId, int[] optionIndices, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("poll_id", pollId);
            JSONArray indices = new JSONArray();
            for (int i : optionIndices) indices.put(i);
            body.put("options", indices);
            post("/api/polls/votePoll", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void closePoll(long pollId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("poll_id", pollId);
            post("/api/polls/closePoll", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getPollResults(long pollId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("poll_id", pollId);
            post("/api/polls/getPollResults", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Chat Folders ────────────────────────────────────────────────────

    public static void createFolder(String title, long[] chatIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("title", title);
            JSONArray ids = new JSONArray();
            for (long id : chatIds) ids.put(id);
            body.put("chat_ids", ids);
            post("/api/folders/createFolder", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void editFolder(long folderId, String title, long[] chatIds, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("folder_id", folderId);
            if (title != null) body.put("title", title);
            if (chatIds != null) {
                JSONArray ids = new JSONArray();
                for (long id : chatIds) ids.put(id);
                body.put("chat_ids", ids);
            }
            post("/api/folders/editFolder", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteFolder(long folderId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("folder_id", folderId);
            post("/api/folders/deleteFolder", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getFolders(ApiCallback callback) {
        post("/api/folders/getFolders", new JSONObject(), callback);
    }

    // ── Topics ──────────────────────────────────────────────────────────

    public static void createTopic(long chatId, String title, String iconEmoji, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("title", title);
            if (iconEmoji != null) body.put("icon_emoji", iconEmoji);
            post("/api/topics/createTopic", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void editTopic(long topicId, String title, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("topic_id", topicId);
            body.put("title", title);
            post("/api/topics/editTopic", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void closeTopic(long topicId, boolean closed, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("topic_id", topicId);
            body.put("closed", closed);
            post("/api/topics/closeTopic", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getTopics(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/topics/getTopics", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Scheduled Messages ──────────────────────────────────────────────

    public static void scheduleMessage(long chatId, String text, long sendAt, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("text", text);
            body.put("send_at", sendAt);
            post("/api/scheduled/scheduleMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getScheduledMessages(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/scheduled/getScheduledMessages", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void deleteScheduledMessage(long messageId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("message_id", messageId);
            post("/api/scheduled/deleteScheduledMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Drafts ──────────────────────────────────────────────────────────

    public static void saveDraft(long chatId, String text, Long replyToMsgId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("text", text);
            if (replyToMsgId != null) body.put("reply_to_msg_id", replyToMsgId);
            post("/api/drafts/saveDraft", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getDraft(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/drafts/getDraft", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void clearDraft(long chatId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            post("/api/drafts/clearDraft", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Admin ───────────────────────────────────────────────────────────

    public static void banUser(long chatId, long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("user_id", userId);
            post("/api/admin/banUser", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void restrictUser(long chatId, long userId, boolean canSendMessages, boolean canSendMedia, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("user_id", userId);
            body.put("can_send_messages", canSendMessages);
            body.put("can_send_media", canSendMedia);
            post("/api/admin/restrictUser", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void promoteAdmin(long chatId, long userId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("user_id", userId);
            post("/api/admin/promoteAdmin", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getAdminLog(long chatId, int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/admin/getAdminLog", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Geolocation ─────────────────────────────────────────────────────

    public static void sendLocation(long chatId, double lat, double lng, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("latitude", lat);
            body.put("longitude", lng);
            post("/api/geo/sendLocation", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void sendLiveLocation(long chatId, double lat, double lng, int period, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("latitude", lat);
            body.put("longitude", lng);
            body.put("period", period);
            post("/api/geo/sendLiveLocation", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void stopLiveLocation(long messageId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("message_id", messageId);
            post("/api/geo/stopLiveLocation", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Payments ─────────────────────────────────────────────────────────

    public static void createInvoice(long chatId, String title, String description, long amount, String currency, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("title", title);
            body.put("description", description);
            body.put("amount", amount);
            body.put("currency", currency);
            post("/api/payments/createInvoice", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void sendPayment(long invoiceId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("invoice_id", invoiceId);
            post("/api/payments/sendPayment", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getPaymentHistory(int offset, int limit, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("offset", offset);
            body.put("limit", limit);
            post("/api/payments/getPaymentHistory", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Typing / Online ─────────────────────────────────────────────────

    public static void setTyping(long chatId, String action, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("chat_id", chatId);
            body.put("action", action);
            post("/api/activity/setTyping", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void setOnlineStatus(boolean online, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("online", online);
            post("/api/activity/setOnlineStatus", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    // ── Bots ────────────────────────────────────────────────────────────

    public static void registerBot(String name, String username, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("name", name);
            body.put("username", username);
            post("/api/bots/registerBot", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void getBotInfo(long botId, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("bot_id", botId);
            post("/api/bots/getBotInfo", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void setBotCommands(long botId, JSONArray commands, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("bot_id", botId);
            body.put("commands", commands);
            post("/api/bots/setBotCommands", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }

    public static void sendBotMessage(long botId, long chatId, String text, ApiCallback callback) {
        try {
            JSONObject body = new JSONObject();
            body.put("bot_id", botId);
            body.put("chat_id", chatId);
            body.put("text", text);
            post("/api/bots/sendBotMessage", body, callback);
        } catch (Exception e) {
            callback.onError(-1, e.getMessage());
        }
    }
}
