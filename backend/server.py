import os
import sys
import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- PATH CONFIGURATION ---
sys.path.append(os.path.dirname(__file__))

# --- YOUR IMPORTS ---
try:
    from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase, check_internet_plagiarism
    PARAPHRASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Paraphrase Engine import failed: {e}")
    PARAPHRASE_AVAILABLE = False

# --- FRIEND'S IMPORTS ---
from modules.semantic_similarity.routes import router as semantic_router

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("python-dotenv not installed")

try:
    from auth.routes import router as auth_router
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

try:
    from database.db_config import initialize_database, db_health_check
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from modules.WSA.wsa_engine import WSAAnalyzer
    analyzer = WSAAnalyzer()
    print("✅ WSA Engine initialized successfully")
except Exception as e:
    print(f"⚠️ WSA Engine initialization failed: {e}")
    analyzer = None

# --- INITIALIZATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sinhala Plagiarism Detection API",
    description="Combined API for Paraphrase, Internet Plagiarism, and Style Analysis",
    version="1.0.0"
)

# --- CORS CONFIGURATION (Merged) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS FOR VALIDATION ---
class ParaphraseRequest(BaseModel):
    sourceText: str
    suspiciousText: str

class InternetRequest(BaseModel):
    studentText: str

class WSARequest(BaseModel):
    text: str

# --- 1. YOUR ROUTES (Migrated to FastAPI) ---

@app.post("/api/check-paraphrase")
async def check_paraphrase_route(data: ParaphraseRequest):
    if not PARAPHRASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Paraphrase Engine not available")
    
    try:
        logger.info(f"📥 Paraphrase Request: Source ({len(data.sourceText)} chars)")
        result = check_paraphrase(data.sourceText, data.suspiciousText)
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-internet")
async def check_internet_route(data: InternetRequest):
    if not PARAPHRASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Plagiarism Engine not available")
    
    try:
        logger.info(f"📡 Received Internet Scan Request ({len(data.studentText)} chars)")
        result = check_internet_plagiarism(data.studentText)
        return result
    except Exception as e:
        logger.error(f"❌ Internet Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. FRIEND'S WSA ROUTE ---

@app.post("/api/check-wsa")
async def check_wsa(data: WSARequest):
    if not analyzer:
        raise HTTPException(status_code=503, detail="WSA Engine not available")
    try:
        # Since this is already an async context, we just await
        result = await analyzer.check_text(data.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. INCLUDED ROUTERS ---
app.include_router(semantic_router, prefix="/api")
if AUTH_AVAILABLE:
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# --- 4. LIFECYCLE & HEALTH ---

@app.on_event("startup")
async def startup_event():
    if DB_AVAILABLE:
        initialize_database()

@app.get("/api/health")
@app.get("/health")
async def health_check():
    db_status = db_health_check() if DB_AVAILABLE else {"status": "not_configured"}
    return {
        "status": "healthy",
        "wsa_engine": "available" if analyzer else "unavailable",
        "paraphrase_engine": "available" if PARAPHRASE_AVAILABLE else "unavailable",
        "database": db_status
    }

@app.get("/")
async def root():
    return {"message": "Combined Plagiarism Detection API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)