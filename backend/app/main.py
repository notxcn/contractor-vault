"""
Contractor Vault - FastAPI Application
Main entry point with CORS and route registration
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.middleware import AuditMiddleware
from app.routers import access_router, credentials_router, audit_router, analytics_router, activity_router, email_router, contractor_router, passkey_router, device_router, secrets_router, discovery_router
from app.routers.sessions import router as sessions_router
from app.routers.auth import router as auth_router
from app.utils.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("contractor_vault")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("=" * 60)
    logger.info("Starting Contractor Vault API...")
    settings = get_settings()
    logger.info(f"Configuration: {settings.app_name}")
    init_db()
    logger.info("Database initialized")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="ShadowKey API",
    description="Secure temporary access management for the extended workforce",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

    # CORS - allow all for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    # Register routers
    app.include_router(access_router)
    app.include_router(credentials_router)
    app.include_router(audit_router)
    app.include_router(analytics_router)
    app.include_router(activity_router)
    app.include_router(email_router)
    app.include_router(contractor_router)
    app.include_router(sessions_router)
    app.include_router(auth_router)
    
    # New acquisition features
    app.include_router(passkey_router)
    app.include_router(device_router)
    app.include_router(secrets_router)
    app.include_router(discovery_router)


    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "app": settings.app_name, "version": "4.0.0"}
    
    @app.get("/", tags=["Root"])
    async def root():
        return {"message": "Contractor Vault API", "docs": "/docs"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
