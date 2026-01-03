"""FastAPI server setup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Decision Engine",
    description="AI-powered trading decision engine for crypto trading copilot",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/ai", tags=["decisions"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Decision Engine",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "decide": "/ai/decide",
            "health": "/health",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("AI Decision Engine starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("AI Decision Engine shutting down")
