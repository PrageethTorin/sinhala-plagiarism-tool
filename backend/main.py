"""
Main FastAPI application for Sinhala Plagiarism Detection Tool
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables")

# Import from your existing semantic_similarity module
from modules.semantic_similarity.routes import router as semantic_router

# Import authentication router
try:
    from auth.routes import router as auth_router
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("Auth module not available")

# Import database configuration
try:
    from database.db_config import initialize_database, db_health_check
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Database module not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sinhala Plagiarism Detection API",
    description="API for detecting plagiarism in Sinhala text",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your existing semantic similarity router
app.include_router(semantic_router, prefix="/api")

# Include authentication router
if AUTH_AVAILABLE:
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    if DB_AVAILABLE:
        try:
            if initialize_database():
                logger.info("Database initialized successfully")
            else:
                logger.warning("Database initialization failed - continuing without database")
        except Exception as e:
            logger.warning(f"Database initialization error: {e} - continuing without database")
    else:
        logger.info("Running without database support")


@app.get("/")
async def root():
    """Root endpoint"""
    google_configured = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("CSE_ID"))
    db_status = db_health_check() if DB_AVAILABLE else {"status": "not_configured"}

    return {
        "message": "Sinhala Plagiarism Detection API",
        "version": "1.0.0",
        "google_api_configured": google_configured,
        "database_status": db_status.get("status", "unknown"),
        "auth_available": AUTH_AVAILABLE,
        "endpoints": {
            "check_plagiarism": "POST /api/check-plagiarism",
            "supervisor_hybrid": "POST /api/supervisor-hybrid",
            "check_file": "POST /api/check-file",
            "web_search_check": "POST /api/web-search-check",
            "comprehensive_check": "POST /api/comprehensive-check",
            "history": "GET /api/history",
            "statistics": "GET /api/statistics",
            "health": "GET /api/health",
            "algorithms": "GET /api/algorithms",
            "auth_register": "POST /api/auth/register",
            "auth_login": "POST /api/auth/login",
            "auth_google": "POST /api/auth/google",
            "auth_me": "GET /api/auth/me",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = db_health_check() if DB_AVAILABLE else {"status": "not_configured"}

    return {
        "status": "healthy",
        "service": "plagiarism-detection",
        "database": db_status,
        "timestamp": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )