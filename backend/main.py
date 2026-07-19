"""
Right Click AI — Backend Server
FastAPI application entry point.
"""

import logging
import sys
import os
import uuid

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from routers import ai, settings
from services.rate_limiter import rate_limiter

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("rightclick-ai")

# --- App ---
app = FastAPI(
    title="Right Click AI",
    description="AI-powered right-click context menu assistant",
    version="0.1.0",
)

# --- Auth Token for Electron ↔ Backend ---
# Since Electron loads from file:// protocol, CORS is not enough.
# We use a shared secret: the backend generates a random token on startup,
# prints it to stdout (where Electron main process captures it), and
# requires it in the X-Auth-Token header for all /api/* requests.
AUTH_TOKEN = str(uuid.uuid4())
print(f"AUTH_TOKEN: {AUTH_TOKEN}", flush=True)


class AuthTokenMiddleware(BaseHTTPMiddleware):
    """Middleware that validates X-Auth-Token on /api routes."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api"):
            token = request.headers.get("X-Auth-Token")
            if token != AUTH_TOKEN:
                raise HTTPException(status_code=403, detail="Forbidden")
        return await call_next(request)


# CORS — allow only the Electron renderer (file:// sends Origin: null)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth token middleware (must be added after CORS)
app.add_middleware(AuthTokenMiddleware)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter middleware for /api/ai/action endpoint."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/ai/action" and request.method == "POST":
            client_ip = request.client.host if request.client else "127.0.0.1"
            if not rate_limiter.allow(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again in a moment.",
                )
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# --- Routers ---
app.include_router(ai.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return {
        "app": "Right Click AI",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Entry Point ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
        log_level="info",
    )
