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
from app.routers import auth, chats, contacts, media, messages, updates, users


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

# ── Register routers ──────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(media.router)
app.include_router(updates.router)


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
