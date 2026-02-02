"""
EKoder Web API - FastAPI Application
Clinical coding assistant for Australian Emergency Departments
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings, validate_settings
from app.coding.routes import router as coding_router
from app.coding.retriever import retriever
from app.auth.routes import router as auth_router
from app.auth.user_store import init_default_admin
from app.audit.routes import router as audit_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize retriever and auth on startup"""
    logger.info("Starting EKoder Web API...")
    validate_settings()
    retriever.initialize()
    init_default_admin()
    logger.info("EKoder ready!")
    yield
    logger.info("Shutting down EKoder...")


# Create FastAPI app
app = FastAPI(
    title="EKoder Web API",
    description="ICD-10-AM Clinical Coding Assistant for Australian Emergency Departments",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(coding_router)
app.include_router(audit_router)


@app.get("/")
async def root():
    """Serve the frontend or API info"""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "EKoder Web API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/login")
async def login_page():
    """Serve the login page"""
    login_file = frontend_dir / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return {"error": "Login page not found"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Redirect to default swagger UI"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="EKoder API Documentation"
    )
