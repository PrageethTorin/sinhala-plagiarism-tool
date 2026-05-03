import os
import sys
import asyncio
import logging
import atexit
import subprocess
import threading
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import File, UploadFile
from modules.OCR.ocr_engine import extract_text_from_image

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
    
@app.post("/api/ocr-extract")
async def ocr_extract_route(image: UploadFile = File(...)):
    """
    Receives an image file and returns extracted Sinhala text.
    """
    try:
        # Read the uploaded image bytes
        image_bytes = await image.read()
        
        logger.info(f"📸 Received OCR Request: {image.filename}")
        
        # Process via the OCR engine
        extracted_text = extract_text_from_image(image_bytes)
        
        if extracted_text is None:
            raise HTTPException(status_code=500, detail="OCR processing failed")
            
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No readable Sinhala text found in image")

        return {"extractedText": extracted_text}

    except Exception as e:
        logger.error(f"❌ OCR Route Error: {e}")
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


_isolated_stack_proc = None


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _venv_python():
    root = _repo_root()
    candidate = os.path.join(root, ".venv", "Scripts", "python.exe")
    if os.path.exists(candidate):
        return candidate
    return sys.executable


def _stream_child_output(prefix, pipe):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            msg = f"[{prefix}] {line.rstrip()}"
            try:
                print(msg)
            except UnicodeEncodeError:
                print(msg.encode("ascii", errors="replace").decode("ascii"))
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _start_isolated_plagiarism_stack():
    """
    Start the separate run_all.py plagiarism stack without mixing it into this app.

    This old combined backend keeps port 5000. The isolated stack keeps its own
    WSA/Semantic/Paraphrase/Gateway services on 8001/8002/5001/8000.
    """
    global _isolated_stack_proc

    if os.getenv("START_ISOLATED_PLAGIARISM_STACK", "1") == "0":
        print("Isolated plagiarism stack disabled (START_ISOLATED_PLAGIARISM_STACK=0)")
        return None

    if _isolated_stack_proc and _isolated_stack_proc.poll() is None:
        return _isolated_stack_proc

    root = _repo_root()
    py = _venv_python()
    env = os.environ.copy()

    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("GATEWAY_PORT", "8000")
    env.setdefault("WSA_PORT", "8001")
    env.setdefault("SEMANTIC_PORT", "8002")
    env["PARAPHRASE_PORT"] = os.getenv("PLAGIARISM_PARAPHRASE_PORT", "5001")
    env["PARAPHRASE_API_URL"] = f"http://127.0.0.1:{env['PARAPHRASE_PORT']}"
    env["WSA_API_URL"] = f"http://127.0.0.1:{env['WSA_PORT']}"
    env["SEMANTIC_API_URL"] = f"http://127.0.0.1:{env['SEMANTIC_PORT']}"

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    _isolated_stack_proc = subprocess.Popen(
        [py, os.path.join(root, "run_all.py")],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
    )

    if _isolated_stack_proc.stdout is not None:
        threading.Thread(
            target=_stream_child_output,
            args=("RUN_ALL", _isolated_stack_proc.stdout),
            daemon=True,
        ).start()

    print("Started isolated plagiarism stack through run_all.py")
    return _isolated_stack_proc


def _stop_isolated_plagiarism_stack():
    global _isolated_stack_proc
    if _isolated_stack_proc and _isolated_stack_proc.poll() is None:
        try:
            _isolated_stack_proc.terminate()
        except Exception:
            pass


atexit.register(_stop_isolated_plagiarism_stack)


if __name__ == "__main__":
    import uvicorn
    _start_isolated_plagiarism_stack()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SERVER_PORT", "5000")), reload=False)
