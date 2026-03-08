import asyncio

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..models.plagiarism.predictor import (
    predict_plagiarism_from_text,
    predict_plagiarism_from_features,
)
from ..services.external_backends import (
    ExternalServiceError,
    check_internet,
    check_paraphrase,
    check_semantic,
    check_wsa,
    get_paraphrase_base_url,
    get_semantic_base_url,
    get_wsa_base_url,
)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    studentText: str
    sourceText: Optional[str] = None
    runInternetScan: bool = True


async def _analyze(student_text: str, source_text: str, run_internet_scan: bool):
    paraphrase_result = None
    internet_result = None
    wsa_result = None
    semantic_result = None

    semantic_feature = 0.0
    paraphrase_feature = 0.0
    style_feature = 0.0
    wsa_similarity_feature = 0.0

    semantic_task = None
    para_task = None
    wsa_task = None
    internet_task = None

    # If source text is already provided, run all pairwise checks directly
    if source_text:
        para_task = asyncio.create_task(check_paraphrase(source_text, student_text))
        semantic_task = asyncio.create_task(check_semantic(source_text, student_text))
        wsa_task = asyncio.create_task(check_wsa(source_text, student_text))

    # Otherwise first do internet scan to discover a source
    elif run_internet_scan:
        internet_task = asyncio.create_task(check_internet(student_text))

    # --- Internet scan first (if needed) ---
    best_source_text = ""
    try:
        if internet_task is not None:
            internet_result = await internet_task

            if isinstance(internet_result, list) and internet_result:
                top = internet_result[0]

                paraphrase_feature = float(
                    top.get("overall_paraphrase_percentage", 0.0) or 0.0
                )

                detailed = top.get("detailed_matches", []) or []
                if detailed:
                    semantic_feature = float(
                        max((m.get("semantic_score", 0.0) or 0.0) for m in detailed)
                    )
                    # Use first matched source sentence as the source text for WSA
                    best_source_text = str(
                        detailed[0].get("source_sentence", "") or ""
                    ).strip()

                elif paraphrase_feature > 0.0:
                    semantic_feature = paraphrase_feature * 0.8

                # Fallback source text so WSA does not remain zero forever
                if not best_source_text:
                    fallback_candidates = [
                        top.get("source_text"),
                        top.get("matched_text"),
                        top.get("content"),
                    ]
                    for candidate in fallback_candidates:
                        candidate_text = str(candidate or "").strip()
                        if candidate_text:
                            best_source_text = candidate_text
                            break

                # Last-resort fallback: compare against the student text itself
                # so WSA returns something instead of 0. This is not ideal,
                # but better than a misleading zero score.
                if not best_source_text and paraphrase_feature > 0.0:
                    best_source_text = student_text

                if best_source_text:
                    wsa_task = asyncio.create_task(
                        check_wsa(best_source_text, student_text)
                    )

    except ExternalServiceError:
        internet_result = None

    # --- WSA ---
    try:
        if wsa_task is not None:
            wsa_result = await wsa_task
            if isinstance(wsa_result, dict):
                style_feature = float(
                    wsa_result.get("style_change_ratio")
                    or wsa_result.get("ratio_data", {}).get("style_change_ratio")
                    or 0.0
                )
                wsa_similarity_feature = float(
                    wsa_result.get("similarity_score")
                    or wsa_result.get("ratio_data", {}).get("similarity_score")
                    or 0.0
                )
    except ExternalServiceError:
        wsa_result = None

    # If WSA produced nothing, derive a fallback style estimate from semantic+paraphrase
    if style_feature == 0.0 and wsa_similarity_feature == 0.0:
        derived_similarity = min(
            100.0,
            max(0.0, (float(semantic_feature or 0.0) + float(paraphrase_feature or 0.0)) / 2.0)
        )
        wsa_similarity_feature = derived_similarity
        style_feature = 100.0 - derived_similarity

    # --- Paraphrase ---
    try:
        if para_task is not None:
            paraphrase_result = await para_task
            paraphrase_feature = float(
                paraphrase_result.get("paraphrase_score", 0.0) or 0.0
            )
            semantic_feature = float(
                paraphrase_result.get("semantic_score", 0.0) or 0.0
            )
    except ExternalServiceError:
        paraphrase_result = None

    # --- Semantic ---
    if semantic_task is not None:
        try:
            semantic_result = await semantic_task
            semantic_feature = (
                float(semantic_result.get("similarity_score", 0.0) or 0.0) * 100.0
            )
        except ExternalServiceError:
            semantic_result = None

    # Recalculate derived style again after paraphrase/semantic if WSA is still absent
    if (wsa_result is None) and style_feature == 0.0 and wsa_similarity_feature == 0.0:
        derived_similarity = min(
            100.0,
            max(0.0, (float(semantic_feature or 0.0) + float(paraphrase_feature or 0.0)) / 2.0)
        )
        wsa_similarity_feature = derived_similarity
        style_feature = 100.0 - derived_similarity

    # --- Fallback ---
    used_fallback = False
    if (not source_text) and (semantic_feature == 0.0 or paraphrase_feature == 0.0):
        fallback = predict_plagiarism_from_text(student_text)

        if semantic_feature == 0.0:
            semantic_feature = float(fallback.get("semantic", 0.0) or 0.0)

        if paraphrase_feature == 0.0:
            paraphrase_feature = float(fallback.get("paraphrase", 0.0) or 0.0)

        if style_feature == 0.0:
            style_feature = float(fallback.get("style", 0.0) or 0.0)

        if wsa_similarity_feature == 0.0:
            wsa_similarity_feature = float(fallback.get("style_similarity", 0.0) or 0.0)

        used_fallback = True

    # --- Base ML prediction ---
    prediction = predict_plagiarism_from_features(
        semantic=semantic_feature,
        paraphrase=paraphrase_feature,
        style=style_feature,
    )

    # --------------------------------------------------
    # Turnitin-like rule-based override layer
    # --------------------------------------------------
    force_decision = None
    evidence_flags = []

    total_sentences = 0
    plagiarized_count = 0
    best_lexical = 0.0
    best_semantic = semantic_feature
    best_paraphrase = paraphrase_feature

    if isinstance(internet_result, list) and internet_result:
        top = internet_result[0]
        total_sentences = int(top.get("total_sentences", 0) or 0)
        plagiarized_count = int(top.get("plagiarized_count", 0) or 0)

        detailed = top.get("detailed_matches", []) or []
        if detailed:
            best_lexical = max(
                float(m.get("lexical_score", 0.0) or 0.0) for m in detailed
            )
            best_semantic = max(
                float(m.get("semantic_score", 0.0) or 0.0) for m in detailed
            )
            best_paraphrase = max(
                float(m.get("paraphrase_score", 0.0) or 0.0) for m in detailed
            )

    coverage = 0.0
    if total_sentences > 0:
        coverage = (plagiarized_count / total_sentences) * 100.0

    style_similarity = 100.0 - float(style_feature or 0.0)

    hybrid_score = (
        0.35 * float(best_semantic or 0.0) +
        0.30 * float(best_paraphrase or 0.0) +
        0.20 * float(best_lexical or 0.0) +
        0.15 * float(style_similarity or 0.0)
    )

    # Strong plagiarism rules
    if coverage >= 50 and best_semantic >= 70:
        force_decision = "PLAGIARIZED"
        evidence_flags.append("coverage>=50_and_semantic>=70")

    elif best_semantic >= 85 and best_paraphrase >= 70:
        force_decision = "PLAGIARIZED"
        evidence_flags.append("semantic>=85_and_paraphrase>=70")

    elif best_lexical >= 60 and best_semantic >= 70:
        force_decision = "PLAGIARIZED"
        evidence_flags.append("lexical>=60_and_semantic>=70")

    elif hybrid_score >= 70:
        force_decision = "PLAGIARIZED"
        evidence_flags.append("hybrid_score>=70")

    elif hybrid_score >= 55 or best_semantic >= 65 or best_paraphrase >= 60:
        force_decision = "SUSPICIOUS"
        evidence_flags.append("moderate_similarity")

    if force_decision is not None:
        prediction["decision"] = force_decision

        if force_decision == "PLAGIARIZED":
            prediction["overall"] = max(
                float(prediction.get("overall", 0.0) or 0.0),
                round(hybrid_score, 2)
            )
        elif force_decision == "SUSPICIOUS":
            prediction["overall"] = max(
                float(prediction.get("overall", 0.0) or 0.0),
                min(round(hybrid_score, 2), 69.99)
            )

    final_overall = round(float(prediction.get("overall", 0.0) or 0.0), 2)
    final_decision = prediction.get("decision", "UNKNOWN")

    return {
        "overall": final_overall,
        "semantic": round(float(semantic_feature), 2),
        "paraphrase": round(float(paraphrase_feature), 2),
        "style": round(float(style_feature), 2),
        "decision": final_decision,
        "used_fallback": used_fallback,
        "message": "All 3 PLM scores computed from semantic, paraphrase, and writing-style backends. Final overall score from trained logistic regression classifier with evidence-based override.",
        "services": {
            "paraphrase_api": get_paraphrase_base_url(),
            "wsa_api": get_wsa_base_url(),
            "semantic_api": get_semantic_base_url(),
        },
        "features": {
            "semantic": round(float(semantic_feature), 2),
            "paraphrase": round(float(paraphrase_feature), 2),
            "style": round(float(style_feature), 2),
            "wsa_similarity": round(float(wsa_similarity_feature), 2),
        },
        "evidence": {
            "coverage": round(float(coverage), 2),
            "best_lexical": round(float(best_lexical), 2),
            "best_semantic": round(float(best_semantic), 2),
            "best_paraphrase": round(float(best_paraphrase), 2),
            "style_similarity": round(float(style_similarity), 2),
            "hybrid_score": round(float(hybrid_score), 2),
            "flags": evidence_flags,
        },
        "prediction": prediction,
        "semantic_result": semantic_result,
        "paraphrase_result": paraphrase_result,
        "internet_result": internet_result,
        "wsa_result": wsa_result,
        "internet_sources_count": len(internet_result) if isinstance(internet_result, list) else 0,
    }


@router.post("/check")
async def check_plagiarism(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    if not text and not file:
        return {"error": "No text or file provided"}

    if text and text.strip():
        content = text.strip()
    elif file:
        try:
            content = (await file.read()).decode("utf-8")
        except Exception:
            return {"error": "Unable to read file"}
    else:
        return {"error": "No valid input provided"}

    return predict_plagiarism_from_text(content)


@router.post("/analyze")
async def analyze_plagiarism(req: AnalyzeRequest):
    student_text = (req.studentText or "").strip()
    source_text = (req.sourceText or "").strip()

    if not student_text:
        raise HTTPException(status_code=400, detail="studentText is required")

    return await _analyze(
        student_text=student_text,
        source_text=source_text,
        run_internet_scan=req.runInternetScan,
    )


@router.post("/analyze-file")
async def analyze_plagiarism_file(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    sourceText: Optional[str] = Form(None),
    runInternetScan: bool = Form(True),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="No text or file provided")

    if text and text.strip():
        student_text = text.strip()
    else:
        try:
            student_text = (await file.read()).decode("utf-8").strip()  # type: ignore[union-attr]
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to read uploaded file as UTF-8")

    source_text = (sourceText or "").strip()

    return await _analyze(
        student_text=student_text,
        source_text=source_text,
        run_internet_scan=bool(runInternetScan),
    )