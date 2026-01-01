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

@app.get("/")
async def root():
    """Root endpoint"""
    google_configured = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("CSE_ID"))

    return {
        "message": "Sinhala Plagiarism Detection API",
        "version": "1.0.0",
        "google_api_configured": google_configured,
        "endpoints": {
            "check_plagiarism": "POST /api/check-plagiarism",
            "supervisor_hybrid": "POST /api/supervisor-hybrid",
            "check_file": "POST /api/check-file",
            "web_search_check": "POST /api/web-search-check",
            "comprehensive_check": "POST /api/comprehensive-check",
            "health": "GET /api/health",
            "algorithms": "GET /api/algorithms",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "plagiarism-detection",
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