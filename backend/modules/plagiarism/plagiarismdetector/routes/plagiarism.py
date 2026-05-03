import asyncio
import re
import unicodedata

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..models.plagiarism.predictor import (
    predict_plagiarism_from_text,
    predict_plagiarism_from_features,
)
from ..services.external_backends import (
    ExternalServiceError,
    check_paraphrase,
    check_semantic,
    check_wsa,
    get_paraphrase_base_url,
    get_semantic_base_url,
    get_wsa_base_url,
)
from ..services.db_compare_service import analyze_against_db
from ..services.web_scan import check_internet_plagiarism

router = APIRouter()


def _normalize_for_coverage(text: str) -> str:
    value = unicodedata.normalize("NFC", str(text or "")).casefold()
    value = re.sub(r"[\u200b-\u200f\ufeff]", "", value)
    cleaned = []
    for char in value:
        category = unicodedata.category(char)
        cleaned.append(" " if category[0] in {"P", "S"} else char)
    return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def _score(match: dict, key: str) -> float:
    try:
        return float(match.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _is_direct_web_match(match: dict) -> bool:
    lexical = _score(match, "lexical_score")
    semantic = _score(match, "semantic_score")
    paraphrase = _score(match, "paraphrase_score")
    mode = str(match.get("mode", "") or "").lower()

    return (
        mode == "high-lexical"
        or lexical >= 82.0
        or (lexical >= 75.0 and semantic >= 70.0 and paraphrase >= 75.0)
    )


def _is_paraphrased_web_match(match: dict) -> bool:
    if _is_direct_web_match(match):
        return False

    lexical = _score(match, "lexical_score")
    semantic = _score(match, "semantic_score")
    paraphrase = _score(match, "paraphrase_score")

    return (
        semantic >= 70.0
        and paraphrase >= 55.0
        and lexical < 70.0
        and (semantic - lexical) >= 10.0
    )


def _matched_text_coverage(student_text: str, detailed_matches, predicate=None) -> float:
    student_norm = _normalize_for_coverage(student_text)
    if not student_norm or not detailed_matches:
        return 0.0

    spans = []
    for match in detailed_matches:
        if predicate is not None and not predicate(match):
            continue

        matched_text = (
            match.get("student_sentence")
            or match.get("input_sentence")
            or match.get("matched_text")
            or ""
        )
        matched_norm = _normalize_for_coverage(matched_text)
        if len(matched_norm) < 12:
            continue

        start = student_norm.find(matched_norm)
        if start >= 0:
            spans.append((start, start + len(matched_norm)))
        elif student_norm in matched_norm:
            spans.append((0, len(student_norm)))

    if not spans:
        return 0.0

    spans.sort()
    merged = []
    for start, end in spans:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    covered = sum(end - start for start, end in merged)
    return min(1.0, covered / len(student_norm))


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
    web_direct_feature = 0.0
    web_related_feature = 0.0
    style_feature = 0.0
    wsa_similarity_feature = 0.0
    web_match_type = "none"
    text_coverage = 0.0
    direct_text_coverage = 0.0
    paraphrase_text_coverage = 0.0

    semantic_task = None
    para_task = None
    wsa_task = None
    internet_task = None

    if not source_text and not run_internet_scan:
        return await analyze_against_db(student_text)

    # If source text is already provided, run all pairwise checks directly
    if source_text:
        para_task = asyncio.create_task(check_paraphrase(source_text, student_text))
        semantic_task = asyncio.create_task(check_semantic(source_text, student_text))
        wsa_task = asyncio.create_task(check_wsa(source_text, student_text))

    # Otherwise first do internet scan to discover a source
    elif run_internet_scan:
        internet_task = asyncio.create_task(
            asyncio.to_thread(check_internet_plagiarism, student_text)
        )

    # --- Internet scan first (if needed) ---
    best_source_text = ""
    try:
        if internet_task is not None:
            internet_result = await internet_task

            if isinstance(internet_result, list) and internet_result:
                top = internet_result[0]

                web_related_feature = float(
                    top.get("overall_paraphrase_percentage", 0.0) or 0.0
                )

                detailed = top.get("detailed_matches", []) or []
                if detailed:
                    text_coverage = max(
                        text_coverage,
                        _matched_text_coverage(student_text, detailed)
                    )
                    direct_text_coverage = max(
                        direct_text_coverage,
                        _matched_text_coverage(student_text, detailed, _is_direct_web_match)
                    )
                    paraphrase_text_coverage = max(
                        paraphrase_text_coverage,
                        _matched_text_coverage(student_text, detailed, _is_paraphrased_web_match)
                    )
                    semantic_scores = [
                        _score(m, "semantic_score")
                        for m in detailed
                    ]
                    lexical_scores = [
                        _score(m, "lexical_score")
                        for m in detailed
                    ]
                    paraphrase_scores = [
                        _score(m, "paraphrase_score")
                        for m in detailed
                    ]

                    semantic_feature = float(
                        max(semantic_scores) if semantic_scores else 0.0
                    )

                    direct_scores = []
                    true_paraphrase_scores = []
                    for m, lexical_score, semantic_score, paraphrase_score in zip(
                        detailed, lexical_scores, semantic_scores, paraphrase_scores
                    ):
                        if _is_direct_web_match(m):
                            direct_scores.append(max(lexical_score, paraphrase_score))
                        elif _is_paraphrased_web_match(m):
                            true_paraphrase_scores.append(paraphrase_score)

                    web_direct_feature = max(direct_scores) if direct_scores else 0.0
                    paraphrase_feature = (
                        max(true_paraphrase_scores) if true_paraphrase_scores else 0.0
                    )

                    # Use first matched source sentence as the source text for WSA
                    best_source_text = str(
                        detailed[0].get("source_sentence", "") or ""
                    ).strip()

                elif web_related_feature > 0.0:
                    semantic_feature = web_related_feature * 0.8

                exact_density = float(top.get("exact_density", 0.0) or 0.0)
                match_density = float(top.get("match_density", 0.0) or 0.0)
                coverage_copy_signal = (
                    direct_text_coverage >= 0.35
                    and web_direct_feature >= 75.0
                )
                paraphrase_signal = (
                    paraphrase_text_coverage >= 0.35
                    and paraphrase_feature >= 55.0
                )

                if coverage_copy_signal:
                    web_direct_feature = max(web_direct_feature, 85.0, web_related_feature)
                    web_match_type = "direct_copy"
                elif exact_density >= 0.35 or web_direct_feature >= 80.0:
                    web_match_type = "direct_copy"
                    web_direct_feature = max(web_direct_feature, web_related_feature)
                elif paraphrase_signal or paraphrase_feature >= 60.0:
                    web_match_type = "paraphrase"
                elif match_density >= 0.35 or semantic_feature >= 65.0:
                    web_match_type = "semantic_web_match"
                elif web_related_feature > 0.0:
                    web_match_type = "weak_web_match"

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
                if not best_source_text and web_related_feature > 0.0:
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
        content_match_feature = max(float(paraphrase_feature or 0.0), float(web_direct_feature or 0.0))
        derived_similarity = min(
            100.0,
            max(0.0, (float(semantic_feature or 0.0) + content_match_feature) / 2.0)
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
        content_match_feature = max(float(paraphrase_feature or 0.0), float(web_direct_feature or 0.0))
        derived_similarity = min(
            100.0,
            max(0.0, (float(semantic_feature or 0.0) + content_match_feature) / 2.0)
        )
        wsa_similarity_feature = derived_similarity
        style_feature = 100.0 - derived_similarity

    # --- Fallback ---
    used_fallback = False
    if (
        (not source_text)
        and semantic_feature == 0.0
        and paraphrase_feature == 0.0
        and web_direct_feature == 0.0
    ):
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
        paraphrase=max(paraphrase_feature, web_direct_feature),
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
    best_direct = web_direct_feature
    exact_density = 0.0
    match_density = 0.0

    if isinstance(internet_result, list) and internet_result:
        top = internet_result[0]
        total_sentences = int(top.get("total_sentences", 0) or 0)
        plagiarized_count = int(top.get("plagiarized_count", 0) or 0)
        exact_density = float(top.get("exact_density", 0.0) or 0.0)
        match_density = float(top.get("match_density", 0.0) or 0.0)

        detailed = top.get("detailed_matches", []) or []
        if detailed:
            text_coverage = max(
                text_coverage,
                _matched_text_coverage(student_text, detailed)
            )
            direct_text_coverage = max(
                direct_text_coverage,
                _matched_text_coverage(student_text, detailed, _is_direct_web_match)
            )
            paraphrase_text_coverage = max(
                paraphrase_text_coverage,
                _matched_text_coverage(student_text, detailed, _is_paraphrased_web_match)
            )
            best_lexical = max(
                _score(m, "lexical_score") for m in detailed
            )
            best_semantic = max(
                _score(m, "semantic_score") for m in detailed
            )
            best_paraphrase = max(
                _score(m, "paraphrase_score") for m in detailed
            )
            direct_candidates = [
                max(
                    _score(m, "lexical_score"),
                    _score(m, "paraphrase_score"),
                )
                for m in detailed
                if _is_direct_web_match(m)
            ]
            if direct_candidates:
                best_direct = max(best_direct, max(direct_candidates))

    coverage = 0.0
    if total_sentences > 0:
        coverage = (plagiarized_count / total_sentences) * 100.0
    coverage = max(coverage, text_coverage * 100.0)

    style_similarity = 100.0 - float(style_feature or 0.0)

    coverage_copy_signal = (
        direct_text_coverage >= 0.35
        and max(best_direct, web_direct_feature) >= 75.0
    )
    paraphrase_signal = (
        paraphrase_text_coverage >= 0.35
        and best_paraphrase >= 55.0
        and best_lexical < 70.0
    )

    if coverage_copy_signal:
        best_direct = max(best_direct, 85.0, web_related_feature)
        web_direct_feature = max(web_direct_feature, best_direct)
        web_match_type = "direct_copy"
    elif exact_density >= 0.35 or best_direct >= 80.0:
        web_match_type = "direct_copy"
    elif paraphrase_signal or web_match_type == "paraphrase":
        web_match_type = "paraphrase"

    hybrid_score = (
        0.30 * float(best_semantic or 0.0) +
        0.25 * float(paraphrase_feature or 0.0) +
        0.25 * float(best_direct or 0.0) +
        0.05 * float(best_lexical or 0.0) +
        0.15 * float(style_similarity or 0.0)
    )

    # Strong plagiarism rules. Semantic similarity alone is not enough here:
    # direct copy needs lexical/exact evidence; paraphrase stays suspicious.
    if best_direct >= 85 or exact_density >= 0.40 or coverage_copy_signal:
        force_decision = "PLAGIARIZED"
        evidence_flags.append("direct_web_copy")

    elif paraphrase_signal:
        force_decision = "SUSPICIOUS"
        evidence_flags.append("paraphrased_web_match")

    elif web_match_type == "paraphrase":
        force_decision = "SUSPICIOUS"
        evidence_flags.append("possible_paraphrased_web_match")

    elif hybrid_score >= 70 and best_lexical >= 70 and coverage >= 50:
        force_decision = "SUSPICIOUS"
        evidence_flags.append("strong_non_exact_web_match")

    elif (
        hybrid_score >= 55
        or (best_paraphrase >= 60 and paraphrase_text_coverage >= 0.20)
    ):
        force_decision = "SUSPICIOUS"
        evidence_flags.append("moderate_similarity")

    if force_decision is not None:
        prediction["decision"] = force_decision

        if force_decision == "PLAGIARIZED":
            prediction["overall"] = max(
                float(prediction.get("overall", 0.0) or 0.0),
                round(hybrid_score, 2),
                round(best_direct, 2),
                round(coverage, 2),
                80.0,
            )
        elif force_decision == "SUSPICIOUS":
            suspicious_score = max(
                float(prediction.get("overall", 0.0) or 0.0),
                round(hybrid_score, 2),
                round(best_paraphrase * 0.8, 2),
                round(paraphrase_text_coverage * 65.0, 2),
                45.0 if paraphrase_signal else 0.0,
            )
            prediction["overall"] = max(
                float(prediction.get("overall", 0.0) or 0.0),
                min(suspicious_score, 69.99)
            )

    final_overall = round(float(prediction.get("overall", 0.0) or 0.0), 2)
    final_decision = prediction.get("decision", "UNKNOWN")

    return {
        "overall": final_overall,
        "semantic": round(float(semantic_feature), 2),
        "paraphrase": round(float(paraphrase_feature), 2),
        "web_direct_match": round(float(web_direct_feature), 2),
        "web_match_type": web_match_type,
        "style": round(float(style_feature), 2),
        "decision": final_decision,
        "used_fallback": used_fallback,
        "message": "Final score separates direct copying, paraphrased web matches, and related-topic matches.",
        "services": {
            "paraphrase_api": get_paraphrase_base_url(),
            "wsa_api": get_wsa_base_url(),
            "semantic_api": get_semantic_base_url(),
        },
        "features": {
            "semantic": round(float(semantic_feature), 2),
            "paraphrase": round(float(paraphrase_feature), 2),
            "web_direct_match": round(float(web_direct_feature), 2),
            "web_related": round(float(web_related_feature), 2),
            "web_match_type": web_match_type,
            "style": round(float(style_feature), 2),
            "wsa_similarity": round(float(wsa_similarity_feature), 2),
        },
        "evidence": {
            "coverage": round(float(coverage), 2),
            "exact_density": round(float(exact_density), 4),
            "match_density": round(float(match_density), 4),
            "text_coverage": round(float(text_coverage), 4),
            "direct_text_coverage": round(float(direct_text_coverage), 4),
            "paraphrase_text_coverage": round(float(paraphrase_text_coverage), 4),
            "best_lexical": round(float(best_lexical), 2),
            "best_semantic": round(float(best_semantic), 2),
            "best_paraphrase": round(float(best_paraphrase), 2),
            "best_direct": round(float(best_direct), 2),
            "classified_paraphrase": round(float(paraphrase_feature), 2),
            "web_match_type": web_match_type,
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
