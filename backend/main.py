"""
shortcutAI — Backend Server
FastAPI application entry point.
"""

import logging
import sys
import os
import uuid

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
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
    title="shortcutAI",
    description="AI-powered right-click context menu assistant",
    version="0.1.0",
)

# --- Auth Token for Electron ↔ Backend ---
AUTH_TOKEN = str(uuid.uuid4())
print(f"AUTH_TOKEN: {AUTH_TOKEN}", flush=True)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Combined auth + rate limit middleware (avoids BaseHTTPMiddleware nesting issues)."""
    # Auth: require X-Auth-Token on all /api/* routes
    if request.url.path.startswith("/api"):
        token = request.headers.get("X-Auth-Token")
        if token != AUTH_TOKEN:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # Rate limit: only for /api/ai/action POST
    if request.url.path == "/api/ai/action" and request.method == "POST":
        client_ip = request.client.host if request.client else "127.0.0.1"
        if not rate_limiter.allow(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    return await call_next(request)


# CORS — allow only the Electron renderer (file:// sends Origin: null)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(ai.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return {
        "app": "shortcutAI",
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
