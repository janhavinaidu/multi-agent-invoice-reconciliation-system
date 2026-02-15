"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.core.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent AI Powered Invoice Processing System",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# -------------------------
# CORS middleware (FIXED)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for now)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    
    # Initialize services
    from app.services.agent_service import get_agent_service
    from app.services.processing_service import get_processing_service
    
    agent_service = get_agent_service()
    processing_service = get_processing_service()
    
    logger.info(f"Loaded {len(agent_service.po_database)} purchase orders")
    logger.info("Services initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")


# For local development only
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   # ✅ fixed import path
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
