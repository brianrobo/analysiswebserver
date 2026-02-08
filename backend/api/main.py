"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.core.cache import cache
from api.db.session import init_db


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Web-based analysis tool with multiple utilities",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database tables and Redis cache on startup
    """
    init_db()
    await cache.connect()
    print(f"✓ {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"✓ Database initialized")
    print(f"✓ Redis cache connected")
    print(f"✓ API docs available at: /api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Close Redis connection on shutdown
    """
    await cache.disconnect()
    print(f"✓ Redis cache disconnected")
    print(f"✓ {settings.APP_NAME} shut down gracefully")


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Import and include routers
from api.routes import auth, settings, analysis, websocket, download

app.include_router(auth.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(analysis.router)
app.include_router(download.router)  # Download routes (included in /api/v1/analysis)
app.include_router(websocket.router)  # WebSocket routes (no /api/v1 prefix)
