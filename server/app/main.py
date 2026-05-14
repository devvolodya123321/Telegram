"""
Custom Messenger Server — drop-in replacement for Telegram backend.

Run:
    cd server
    pip install -r requirements.txt
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8443 --reload
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db

# ── Karatelishak handlers ─────────────────────────────────────────────────
from app.Karatelishak import (
    sendCode,
    signIn,
    signUp,
    logOut,
    setPassword,
    checkPassword,
    deleteAccount,
    getMe,
    getUser,
    getUsers,
    updateProfile,
    updateUsername,
    setProfilePhoto,
    deleteProfilePhoto,
    getProfilePhotos,
    setPrivacy,
    getPrivacy,
    importContacts,
    getContacts,
    searchContacts,
    deleteContacts,
    blockUser,
    unblockUser,
    getBlocked,
    createChat,
    createChannel,
    editTitle,
    editDescription,
    setChatPhoto,
    addUser,
    deleteUser,
    getFullChat,
    getMembers,
    leaveChat,
    startPrivate,
    joinChat,
    pinMessage,
    unpinMessage,
    sendMessage,
    getHistory,
    getDialogs,
    readHistory,
    deleteMessages,
    editMessage,
    forwardMessages,
    searchMessages,
    getPinnedMessages,
    requestCall,
    acceptCall,
    discardCall,
    setCallRating,
    getCallHistory,
    createStickerSet,
    addStickerToSet,
    getStickerSets,
    removeStickerSet,
    sendSticker,
    sendReaction,
    getReactions,
    postStory,
    getStories,
    deleteStory,
    viewStory,
    setNotificationSettings,
    getNotificationSettings,
    muteChat,
    unmuteChat,
    uploadFile,
    downloadFile,
    sendMedia,
    websocketUpdates,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all Karatelishak routers ─────────────────────────────────────
_handlers = [
    # Auth
    sendCode, signIn, signUp, logOut, setPassword, checkPassword, deleteAccount,
    # Users / Profile
    getMe, getUser, getUsers, updateProfile, updateUsername,
    setProfilePhoto, deleteProfilePhoto, getProfilePhotos, setPrivacy, getPrivacy,
    # Contacts
    importContacts, getContacts, searchContacts, deleteContacts, blockUser, unblockUser, getBlocked,
    # Chats
    createChat, createChannel, editTitle, editDescription, setChatPhoto,
    addUser, deleteUser, getFullChat, getMembers, leaveChat, startPrivate, joinChat,
    pinMessage, unpinMessage,
    # Messages
    sendMessage, getHistory, getDialogs, readHistory, deleteMessages,
    editMessage, forwardMessages, searchMessages, getPinnedMessages,
    # Calls
    requestCall, acceptCall, discardCall, setCallRating, getCallHistory,
    # Stickers
    createStickerSet, addStickerToSet, getStickerSets, removeStickerSet, sendSticker,
    # Reactions
    sendReaction, getReactions,
    # Stories
    postStory, getStories, deleteStory, viewStory,
    # Notifications
    setNotificationSettings, getNotificationSettings, muteChat, unmuteChat,
    # Media
    uploadFile, downloadFile, sendMedia,
    # WebSocket
    websocketUpdates,
]

for handler in _handlers:
    app.include_router(handler.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}
