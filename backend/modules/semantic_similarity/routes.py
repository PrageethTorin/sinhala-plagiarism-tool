# backend/modules/semantic_similarity/routes.py
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

# Local imports - these modules should exist in the same package
from .engine import (
    process_paragraph_similarity,
    process_document_text,
    process_doc_compare,
    process_paragraph_web_check,
)
from .extractors import extract_text_from_bytes
from .websearch import fetch_web_texts_for_document
from .googledoc import fetch_google_doc_text_service

router = APIRouter(tags=["Semantic Similarity"])


# ----------------------------
# Request models
# ----------------------------
class PairParagraph(BaseModel):
    p1: str
    p2: str


class UploadCompareReq(BaseModel):
    doc_text: str
    corpus: List[str] = []
    top_k: int = 3


class DocCompareReq(BaseModel):
    doc_a: str
    doc_b: str
    top_k: int = 3


class ParagraphWebReq(BaseModel):
    paragraph: str
    top_k: int = 3
    google_doc_url: Optional[str] = None
    use_web_search: bool = True


# ----------------------------
# Simple health
# ----------------------------
@router.get("/ping")
def ping():
    return {"status": "ok"}


# ----------------------------
# Paragraph similarity (two paragraphs)
# ----------------------------
@router.post("/api/paragraph_similarity")
def paragraph_similarity(payload: PairParagraph):
    """
    Compare two paragraphs (p1 vs p2) and return similarity metrics.
    Delegates work to engine.process_paragraph_similarity.
    """
    return process_paragraph_similarity(payload.p1, payload.p2)


# ----------------------------
# Upload JSON doc_text -> compare against provided corpus
# ----------------------------
@router.post("/api/upload_and_compare")
def upload_and_compare(payload: UploadCompareReq):
    """
    Accepts raw document text in JSON body and an optional corpus list.
    Returns paragraph-level matches and overall document score.
    """
    return process_document_text(
        payload.doc_text or "",
        corpus=payload.corpus or [],
        top_k=payload.top_k or 3,
    )


# ----------------------------
# Document vs Document comparison (sentence-level)
# ----------------------------
@router.post("/api/doc_compare")
def doc_compare(payload: DocCompareReq):
    """
    Compare two documents (strings) and return matching sentence pairs.
    """
    return process_doc_compare(
        payload.doc_a or "",
        payload.doc_b or "",
        top_k=payload.top_k or 3,
    )


# ----------------------------
# File upload endpoint: extract text, optional web search + Google Doc, then compare
# ----------------------------
@router.post("/api/upload_file_compare")
async def upload_file_compare(
    file: UploadFile = File(...),
    top_k: int = Form(3),
    google_doc_url: Optional[str] = Form(None),
    # frontend sends "1" or "0" as string; accept either string or boolean
    use_web_search: Optional[str] = Form("1"),
):
    """
    Upload a file (.txt, .pdf, .docx). Server extracts text, optionally runs web search
    and Google Doc fetch, then uses process_document_text to compare.
    Returns {"source_count": N, "result": {...}}
    """
    # Read file bytes
    content = await file.read()
    try:
        text = extract_text_from_bytes(file.filename or "", content)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {e}")

    corpus: List[str] = []

    # Determine whether to run web search (frontend may send "1"/"0" or "true"/"false")
    run_web = True
    if isinstance(use_web_search, str):
        if use_web_search.strip() in ("0", "false", "False", ""):
            run_web = False

    if run_web:
        try:
            web_texts = fetch_web_texts_for_document(text)
            if web_texts:
                # extend corpus with web page texts
                corpus.extend(web_texts)
        except Exception as e:
            # don't fail entire request for scraping errors; log and continue
            print("fetch_web_texts_for_document error:", e)

    # If user supplied a Google Doc URL/ID, try to fetch (this requires service account configured)
    if google_doc_url:
        doc_id = None
        try:
            if "/d/" in google_doc_url:
                doc_id = google_doc_url.split("/d/")[1].split("/")[0]
            else:
                doc_id = google_doc_url.strip()
        except Exception:
            doc_id = None

        if doc_id:
            try:
                gtext = fetch_google_doc_text_service(doc_id)
                if gtext:
                    corpus.append(gtext)
            except Exception as e:
                print("fetch_google_doc_text_service error:", e)

    # If no corpus found at all, return a result indicating that
    if not corpus:
        # still run processing to produce paragraph split and zero matches
        result = process_document_text(text, corpus=[], top_k=top_k)
        return {"source_count": 0, "result": result, "note": "No web/doc sources found; compared only to empty corpus."}

    # Run core processor
    result = process_document_text(text, corpus=corpus, top_k=top_k)
    return {"source_count": len(corpus), "result": result}


# ----------------------------
# Paragraph -> Web/Docs quick check (single paragraph)
# ----------------------------
@router.post("/api/paragraph_web_check")
def paragraph_web_check(payload: ParagraphWebReq):
    """
    Given a single paragraph, build a small corpus from web search and/or a Google Doc,
    and return the paragraph matches (top_k).
    Delegates to engine.process_paragraph_web_check which should implement the comparison.
    """
    return process_paragraph_web_check(
        payload.paragraph,
        top_k=payload.top_k,
        google_doc_url=payload.google_doc_url,
        use_web_search=payload.use_web_search,
    )
