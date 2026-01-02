"""
API endpoints for plagiarism detection
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import time
import logging
from typing import Dict, Optional

from .schemas import SimilarityRequest, SimilarityResult, TextPair
from .services import SimilarityDetector, FileHandler
from .approved_hybrid import ApprovedHybridDetector

# Optional imports for web services
try:
    from modules.semantic_similarity.corpus.web_corpus_service import WebCorpusSimilarityService
    CORPUS_SERVICE_AVAILABLE = True
except ImportError:
    CORPUS_SERVICE_AVAILABLE = False

try:
    from .web.web_search_service import WebPlagiarismChecker
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# Optional database import
try:
    from database.db_config import save_check, get_history, get_statistics, db_health_check
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
similarity_detector = SimilarityDetector()
file_handler = FileHandler()


# STANDARD PLAGIARISM CHECK 


@router.post("/check-plagiarism", response_model=SimilarityResult)
async def check_plagiarism(request: SimilarityRequest):
    start_time = time.time()

    try:
        result = similarity_detector.calculate_similarity(
            text1=request.text_pair.original,
            text2=request.text_pair.suspicious,
            algorithm=request.algorithm
        )

        is_plagiarized = result["similarity_score"] >= request.threshold

        if result["similarity_score"] >= 0.9:
            verdict = "Plagiarized"
        elif result["similarity_score"] >= request.threshold:
            verdict = "Suspected Plagiarism"
        else:
            verdict = "Original"

        confidence = min(result["similarity_score"] * 1.2, 1.0)
        processing_time = time.time() - start_time

        return SimilarityResult(
            similarity_score=result["similarity_score"],
            is_plagiarized=is_plagiarized,
            confidence=confidence,
            verdict=verdict,
            components=result["components"],
            matches=result["matches"],
            metadata={
                "algorithm_used": request.algorithm,
                "threshold_applied": request.threshold,
                "text_length_original": len(request.text_pair.original),
                "text_length_suspicious": len(request.text_pair.suspicious)
            },
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error in plagiarism check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#  HYBRID ENDPOINT 


@router.post("/supervisor-hybrid")
async def supervisor_hybrid_check(request: SimilarityRequest):
    start_time = time.time()

    try:
        hybrid_detector = ApprovedHybridDetector()

        result = hybrid_detector.detect(
            request.text_pair.original,
            request.text_pair.suspicious
        )

        # Use final_score for decisions
        is_plagiarized = result["final_score"] >= request.threshold

        if result["final_score"] >= 0.9:
            verdict = "Plagiarized"
        elif result["final_score"] >= request.threshold:
            verdict = "Suspected Plagiarism"
        else:
            verdict = "Original"

        # Confidence logic (clean & explainable)
        if result["case_type"] != "difficult":
            confidence = 0.9
        else:
            confidence = 0.7

        processing_time = time.time() - start_time

        components = {
            "custom_score": result["custom_score"],
            "final_score": result["final_score"]
        }
        if result["embedding_score"] is not None:
            components["embedding_score"] = result["embedding_score"]

        metadata = {
            "method": result["method"],
            "case_type": result["case_type"],
            "threshold_applied": request.threshold,
            "algorithm_used": "approved-hybrid",
            "text_length_original": len(request.text_pair.original),
            "text_length_suspicious": len(request.text_pair.suspicious)
        }

        response = {
            "success": True,
            "similarity_score": result["final_score"],
            "is_plagiarized": is_plagiarized,
            "verdict": verdict,
            "confidence": confidence,
            "components": components,
            "matches": [],
            "metadata": metadata,
            "processing_time": processing_time
        }

        # Save to database if available
        if DB_AVAILABLE:
            try:
                save_check(
                    check_type="direct",
                    original_text=request.text_pair.original,
                    suspicious_text=request.text_pair.suspicious,
                    similarity_score=result["final_score"],
                    is_plagiarized=is_plagiarized,
                    algorithm_used="approved-hybrid",
                    threshold_applied=request.threshold,
                    processing_time=processing_time,
                    components=components,
                    metadata=metadata
                )
            except Exception as db_err:
                logger.warning(f"Failed to save to database: {db_err}")

        return response

    except Exception as e:
        logger.error(f"Hybrid detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# FILE-BASED ENDPOINTS


@router.post("/check-file")
async def check_file_plagiarism(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    threshold: float = 0.7,
    algorithm: str = "hybrid"
):
    try:
        text1 = await file_handler.read_file(file1)
        text2 = await file_handler.read_file(file2)

        request = SimilarityRequest(
            text_pair=TextPair(original=text1, suspicious=text2),
            threshold=threshold,
            algorithm=algorithm
        )

        return await check_plagiarism(request)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-file-supervisor-hybrid")
async def check_file_supervisor_hybrid(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    threshold: float = 0.7
):
    try:
        text1 = await file_handler.read_file(file1)
        text2 = await file_handler.read_file(file2)

        request = SimilarityRequest(
            text_pair=TextPair(original=text1, suspicious=text2),
            threshold=threshold,
            algorithm="approved-hybrid"
        )

        return await supervisor_hybrid_check(request)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TEST ENDPOINT 


@router.get("/test-hybrid")
async def test_hybrid_endpoint():
    try:
        hybrid_detector = ApprovedHybridDetector()

        test_cases = [
            {
                "name": "Easy Negative",
                "text1": "මම ගෙදර යමි",
                "text2": "ඔහු පාසලට යයි"
            },
            {
                "name": "Easy Positive",
                "text1": "සිංහල භාෂාව ලංකාවේ ප්රධාන භාෂාවයි",
                "text2": "සිංහල භාෂාව ලංකාවේ ප්රධාන භාෂාවයි"
            },
            {
                "name": "Difficult Case",
                "text1": "ළමයා රෝහල් ගත කරන ලදී",
                "text2": "දරුවා රෝහලට ඇතුළත් කරන ලදී"
            }
        ]

        results = []
        for test in test_cases:
            result = hybrid_detector.detect(test["text1"], test["text2"])

            results.append({
                "test_name": test["name"],
                "similarity_score": result["final_score"],
                "case_type": result["case_type"],
                "method": result["method"],
                "custom_score": result["custom_score"],
                "embedding_score": result["embedding_score"]
            })

        return {"test_results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MISC


@router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@router.get("/performance-stats")
async def get_performance_stats():
    """Get cache and performance statistics"""
    try:
        from .performance import get_performance_stats, get_cache_stats
        return {
            "success": True,
            "stats": get_performance_stats()
        }
    except ImportError:
        return {
            "success": True,
            "stats": {
                "cache_stats": "Performance module not available",
                "timing_stats": {}
            }
        }

@router.get("/algorithms")
async def get_algorithms():
    return {
        "algorithms": [
            {"id": "semantic", "name": "Semantic Similarity"},
            {"id": "lexical", "name": "Lexical Similarity"},
            {"id": "hybrid", "name": "Hybrid"},
            {"id": "approved-hybrid", "name": "Approved Hybrid (Fine-Tuned)"}
        ],
        "endpoints": [
            {"path": "/check-plagiarism", "method": "POST", "description": "Standard plagiarism check"},
            {"path": "/supervisor-hybrid", "method": "POST", "description": "Approved hybrid detection"},
            {"path": "/check-file", "method": "POST", "description": "File-based detection"},
            {"path": "/check-file-supervisor-hybrid", "method": "POST", "description": "File-based hybrid"},
            {"path": "/web-corpus-check", "method": "POST", "description": "FAISS corpus similarity"},
            {"path": "/web-search-check", "method": "POST", "description": "Live Google web search"},
            {"path": "/comprehensive-check", "method": "POST", "description": "Combined check (direct + corpus + web)"},
            {"path": "/test-hybrid", "method": "GET", "description": "Test with predefined cases"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/performance-stats", "method": "GET", "description": "Cache and performance stats"},
            {"path": "/algorithms", "method": "GET", "description": "List algorithms and endpoints"}
        ],
        "web_search_configured": WEB_SEARCH_AVAILABLE,
        "corpus_service_available": CORPUS_SERVICE_AVAILABLE
    }



@router.post("/web-corpus-check")
async def web_corpus_check(request: SimilarityRequest):
    """
    Compares user text against a FAISS-indexed Sinhala web corpus
    using the SAME approved hybrid detection logic.
    """

    if not request.text_pair.original.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    if not CORPUS_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Web corpus service not available. Check corpus configuration."
        )

    try:
        service = WebCorpusSimilarityService()
        matches = service.check(request.text_pair.original)

        # Calculate summary statistics for frontend
        if matches:
            avg_similarity = sum(m.get("final_score", 0) for m in matches) / len(matches)
        else:
            avg_similarity = 0.0

        return {
            "success": True,
            "mode": "web_corpus",
            "input_text": request.text_pair.original,
            "matches": matches,
            "summary": {
                "average_similarity": round(avg_similarity, 4),
                "sources_checked": len(matches),
                "matches_found": len([m for m in matches if m.get("final_score", 0) >= 0.5])
            }
        }
    except Exception as e:
        logger.error(f"Web corpus check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-search-check")
async def web_search_check(request: SimilarityRequest):
    """
    Searches the live web (Google) for potential plagiarism sources
    and compares using the approved hybrid detection logic.

    Requires GOOGLE_API_KEY and CSE_ID environment variables.

    Accepts same format as other endpoints:
    {
        "text_pair": {
            "original": "text to search",
            "suspicious": ""  (optional, not used for web search)
        },
        "threshold": 0.5
    }
    """
    start_time = time.time()

    # Extract text from request (use original text for web search)
    text = request.text_pair.original.strip()
    threshold = request.threshold
    num_results = 5  # Default number of results

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    if not WEB_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Web search service not available"
        )

    try:
        checker = WebPlagiarismChecker()

        if not checker.google_search.is_configured:
            return {
                "success": False,
                "error": "Google API not configured",
                "message": "Set GOOGLE_API_KEY and CSE_ID environment variables",
                "setup_instructions": {
                    "step1": "Go to https://console.cloud.google.com/",
                    "step2": "Create a project and enable Custom Search API",
                    "step3": "Create credentials (API key)",
                    "step4": "Go to https://programmablesearchengine.google.com/",
                    "step5": "Create a search engine and get the ID",
                    "step6": "Set environment variables: GOOGLE_API_KEY and CSE_ID"
                }
            }

        result = checker.check_plagiarism(
            text=text,
            threshold=threshold,
            num_web_results=min(num_results, 10)
        )

        result["processing_time"] = time.time() - start_time
        return result

    except Exception as e:
        logger.error(f"Web search check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive-check")
async def comprehensive_plagiarism_check(request: SimilarityRequest):
    """
    Comprehensive plagiarism check combining:
    1. Direct text comparison (if suspicious text provided)
    2. FAISS corpus search (local)
    3. Live web search (Google API)

    Returns combined results from all sources.
    """
    start_time = time.time()

    if not request.text_pair.original.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    results = {
        "success": True,
        "input_text": request.text_pair.original[:200] + "...",
        "threshold": request.threshold,
        "direct_comparison": None,
        "corpus_matches": [],
        "web_matches": [],
        "overall_verdict": "Original",
        "max_similarity": 0.0
    }

    hybrid_detector = ApprovedHybridDetector()
    max_score = 0.0

    # 1. Direct comparison (if suspicious text provided)
    if request.text_pair.suspicious and request.text_pair.suspicious.strip():
        try:
            direct_result = hybrid_detector.detect(
                request.text_pair.original,
                request.text_pair.suspicious
            )
            results["direct_comparison"] = {
                "similarity_score": direct_result["final_score"],
                "case_type": direct_result["case_type"],
                "method": direct_result["method"],
                "custom_score": direct_result["custom_score"],
                "embedding_score": direct_result.get("embedding_score")
            }
            max_score = max(max_score, direct_result["final_score"])
        except Exception as e:
            logger.error(f"Direct comparison error: {e}")
            results["direct_comparison"] = {"error": str(e)}

    # 2. FAISS corpus search (if available)
    if CORPUS_SERVICE_AVAILABLE:
        try:
            corpus_service = WebCorpusSimilarityService()
            corpus_matches = corpus_service.check(request.text_pair.original)
            results["corpus_matches"] = corpus_matches[:5]

            for match in corpus_matches:
                max_score = max(max_score, match.get("final_score", 0))
        except Exception as e:
            logger.warning(f"Corpus search error: {e}")
            results["corpus_matches"] = [{"error": str(e)}]

    # 3. Live web search (if available and configured)
    if WEB_SEARCH_AVAILABLE:
        try:
            checker = WebPlagiarismChecker()
            if checker.google_search.is_configured:
                web_result = checker.check_plagiarism(
                    request.text_pair.original,
                    threshold=request.threshold,
                    num_web_results=5
                )
                results["web_matches"] = web_result.get("matches", [])[:5]
                results["web_search_enabled"] = True

                for match in web_result.get("matches", []):
                    max_score = max(max_score, match.get("similarity_score", 0))
            else:
                results["web_search_enabled"] = False
                results["web_matches"] = [{"note": "Google API not configured"}]
        except Exception as e:
            logger.warning(f"Web search error: {e}")
            results["web_matches"] = [{"error": str(e)}]

    # Determine overall verdict
    results["max_similarity"] = round(max_score, 4)
    if max_score >= 0.9:
        results["overall_verdict"] = "High Plagiarism Risk"
    elif max_score >= 0.7:
        results["overall_verdict"] = "Moderate Plagiarism Risk"
    elif max_score >= request.threshold:
        results["overall_verdict"] = "Low Plagiarism Risk"
    else:
        results["overall_verdict"] = "Original"

    results["processing_time"] = round(time.time() - start_time, 2)

    # Save to database if available
    if DB_AVAILABLE:
        try:
            save_check(
                check_type="comprehensive",
                original_text=request.text_pair.original,
                suspicious_text=request.text_pair.suspicious,
                similarity_score=max_score,
                is_plagiarized=max_score >= request.threshold,
                algorithm_used="comprehensive",
                threshold_applied=request.threshold,
                processing_time=results["processing_time"],
                components={"direct": results.get("direct_comparison"), "corpus": len(results.get("corpus_matches", []))},
                metadata={"verdict": results["overall_verdict"]}
            )
        except Exception as e:
            logger.warning(f"Failed to save check to database: {e}")

    return results


# DATABASE ENDPOINTS


@router.get("/history")
async def get_check_history(
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    check_type: Optional[str] = Query(None, description="Filter by check type")
):
    """
    Get plagiarism check history from database.

    Returns recent plagiarism checks with their results.
    Supports pagination with limit and offset.
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not configured",
            "message": "MySQL database is not available. History feature requires database setup."
        }

    try:
        history = get_history(limit=limit, offset=offset, check_type=check_type)
        return {
            "success": True,
            "count": len(history),
            "limit": limit,
            "offset": offset,
            "history": history
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_usage_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get plagiarism detection usage statistics.

    Returns:
    - Total checks in period
    - Plagiarized vs original counts
    - Average similarity scores
    - Checks by type breakdown
    """
    if not DB_AVAILABLE:
        return {
            "success": False,
            "error": "Database not configured",
            "message": "MySQL database is not available. Statistics feature requires database setup."
        }

    try:
        stats = get_statistics(days=days)
        return {
            "success": True,
            "period_days": days,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db-health")
async def database_health():
    """Check database connectivity"""
    if not DB_AVAILABLE:
        return {
            "status": "not_configured",
            "message": "Database module not available"
        }

    try:
        return db_health_check()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
