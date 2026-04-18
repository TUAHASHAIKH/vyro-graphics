"""
Grabpic — Intelligent Identity & Retrieval Engine

Main FastAPI application entry point.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import STORAGE_DIR, TEMP_DIR
from app.database import init_db
from app.routers import ingest, auth, images

# ─── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifecycle ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🚀 Starting Grabpic...")
    init_db()
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    logger.info("✅ Database initialized")
    logger.info(f"📁 Storage: {STORAGE_DIR}")
    yield
    logger.info("🛑 Grabpic shutting down.")


# ─── App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Grabpic — Intelligent Identity & Retrieval Engine",
    description="""
**Grabpic** is a high-performance image processing backend designed for large-scale events
like marathons. It uses facial recognition to automatically group images by identity and
provides a **Selfie-as-a-Key** retrieval system.

## Workflow
1. **Ingest** — Upload images or crawl a directory → faces are detected and indexed
2. **Authenticate** — Upload a selfie → receive your unique `grab_id`
3. **Retrieve** — Fetch all your photos using your `grab_id`

## Key Features
- 🔍 Automatic face detection and encoding
- 🆔 Unique `grab_id` per identity (deduplication across images)
- 👥 Multi-face support (one image → many identities)
- 🤳 Selfie-as-a-Key authentication
- 📸 Image retrieval by identity
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(auth.router)
app.include_router(images.router)


# ─── Global Exception Handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please try again.",
        },
    )


# ─── Root & Health ──────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — API overview and health status."""
    return {
        "service": "Grabpic",
        "version": "1.0.0",
        "status": "healthy",
        "description": "Intelligent Identity & Retrieval Engine",
        "docs": "/docs",
        "endpoints": {
            "ingest_upload": "POST /ingest",
            "ingest_crawl": "POST /ingest/crawl",
            "selfie_auth": "POST /auth/selfie",
            "get_images": "GET /images/{grab_id}",
            "serve_image": "GET /image/{image_id}/file",
            "list_faces": "GET /faces",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "grabpic"}
