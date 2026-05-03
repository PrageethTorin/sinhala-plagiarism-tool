import asyncio
import re
from typing import Dict, List, Optional

from ..database.db_config import get_db_connection
from .external_backends import (
    ExternalServiceError,
    check_paraphrase,
    check_semantic,
    get_paraphrase_base_url,
    get_semantic_base_url,
    get_wsa_base_url,
)


SUBMISSIONS_TABLE = "student_submissions"


def _tokenize(text: str) -> List[str]:
    return [w.strip().lower() for w in (text or "").split() if w.strip()]


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return [s.strip() for s in re.split(r'(?<=[.!?।])', text) if s.strip()]


def _normalize_token_db(token: str) -> str:
    token = re.sub(r'^[^\w඀-෿]+|[^\w඀-෿]+$', '', token or '')
    return token.strip().lower()


def _align_words_db(student_sentence: str, source_sentence: str) -> List[Dict]:
    tokens = (student_sentence or '').split()
    source_tokens = [_normalize_token_db(t) for t in (source_sentence or '').split()]
    source_set = {t for t in source_tokens if t}
    aligned = []
    for idx, token in enumerate(tokens):
        norm = _normalize_token_db(token)
        if not norm:
            aligned.append({"token_index": idx, "match_type": "none"})
            continue
        aligned.append({"token_index": idx, "match_type": "exact" if norm in source_set else "none"})
    return aligned


def _build_detailed_matches(student_text: str, source_text: str, overall_score: float) -> List[Dict]:
    student_sents = _split_sentences(student_text)
    source_sents = _split_sentences(source_text)
    if not student_sents or not source_sents:
        return []
    detailed = []
    for i, s_sent in enumerate(student_sents):
        s_tokens = set(_tokenize(s_sent))
        best_score = 0.0
        best_source = None
        for src_sent in source_sents:
            src_tokens = set(_tokenize(src_sent))
            if not s_tokens or not src_tokens:
                continue
            score = len(s_tokens & src_tokens) / len(s_tokens | src_tokens) * 100
            if score > best_score:
                best_score = score
                best_source = src_sent
        if best_score >= 25 and best_source:
            detailed.append({
                "sentenceIndex": i,
                "student_sentence": s_sent,
                "source_sentence": best_source,
                "paraphrase_score": round(max(best_score, overall_score * 0.7), 2),
                "score": round(max(best_score, overall_score * 0.7), 2),
                "aligned_words": _align_words_db(s_sent, best_source),
            })
    return detailed


def _overlap_ratio(a: str, b: str) -> float:
    sa = set(_tokenize(a))
    sb = set(_tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except Exception:
        return float(default)


def _decision_rank(decision: str) -> int:
    return {
        "PLAGIARIZED": 2,
        "SUSPICIOUS": 1,
        "NOT PLAGIARIZED": 0,
    }.get(decision, -1)


def _ensure_table() -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SUBMISSIONS_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text LONGTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4
            """
        )
        conn.commit()
        return True
    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_assignment(text: str) -> Optional[int]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(f"INSERT INTO {SUBMISSIONS_TABLE} (text) VALUES (%s)", (text,))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_previous_assignment(exclude_id: int, limit: int = 300) -> List[Dict]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"""
            SELECT id, text, created_at
            FROM {SUBMISSIONS_TABLE}
            WHERE id <> %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (exclude_id, limit),
        )
        return list(cur.fetchall() or [])
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def _compare_single(student_text: str, source_text: str) -> Dict:
    para_task = asyncio.create_task(check_paraphrase(source_text, student_text))
    sem_task = asyncio.create_task(check_semantic(source_text, student_text))

    paraphrase_result = None
    semantic_result = None

    semantic_feature = 0.0
    paraphrase_feature = 0.0

    try:
        paraphrase_result = await para_task
        paraphrase_feature = _safe_float(paraphrase_result.get("paraphrase_score", 0.0))
        semantic_feature = max(
            semantic_feature,
            _safe_float(paraphrase_result.get("semantic_score", 0.0)),
        )
    except ExternalServiceError:
        paraphrase_result = None

    try:
        semantic_result = await sem_task
        semantic_feature = max(
            semantic_feature,
            _safe_float(semantic_result.get("similarity_score", 0.0)) * 100.0,
        )
    except ExternalServiceError:
        semantic_result = None

    lexical_overlap = _overlap_ratio(student_text, source_text) * 100.0
    content_similarity = max(semantic_feature, paraphrase_feature, lexical_overlap)
    wsa_similarity_feature = content_similarity
    style_feature = 100.0 - content_similarity

    if lexical_overlap >= 90.0:
        decision = "PLAGIARIZED"
        overall = max(content_similarity, 90.0)
        evidence_flag = "direct_db_text_match"
    elif lexical_overlap >= 65.0 or semantic_feature >= 75.0 or paraphrase_feature >= 70.0:
        decision = "SUSPICIOUS"
        overall = max(content_similarity, 55.0)
        evidence_flag = "possible_db_match"
    else:
        decision = "NOT PLAGIARIZED"
        overall = min(content_similarity, 54.99)
        evidence_flag = "weak_db_match"

    return {
        "overall": round(overall, 2),
        "semantic": round(semantic_feature, 2),
        "paraphrase": round(paraphrase_feature, 2),
        "lexical_overlap": round(lexical_overlap, 2),
        "style": round(style_feature, 2),
        "wsa_similarity": round(wsa_similarity_feature, 2),
        "evidence_flag": evidence_flag,
        "decision": decision,
        "paraphrase_result": {
            **(paraphrase_result or {}),
            "detailed_matches": _build_detailed_matches(student_text, source_text, overall),
        },
        "semantic_result": semantic_result,
        "wsa_result": {
            "db_mode": True,
            "similarity_score": round(wsa_similarity_feature, 2),
            "style_change_ratio": round(style_feature, 2),
        },
    }


async def analyze_against_db(student_text: str) -> Dict:
    if not _ensure_table():
        return {
            "overall": 0.0,
            "semantic": 0.0,
            "paraphrase": 0.0,
            "style": 0.0,
            "decision": "NOT PLAGIARIZED",
            "used_fallback": True,
            "message": "DB mode selected, but database connection is unavailable.",
            "services": {
                "paraphrase_api": get_paraphrase_base_url(),
                "wsa_api": get_wsa_base_url(),
                "semantic_api": get_semantic_base_url(),
            },
            "features": {"semantic": 0.0, "paraphrase": 0.0, "style": 0.0, "wsa_similarity": 0.0},
            "evidence": {"flags": ["db_unavailable"]},
            "prediction": {},
            "semantic_result": None,
            "paraphrase_result": None,
            "internet_result": [],
            "wsa_result": None,
            "internet_sources_count": 0,
            "source_status": {
                "score_reliable": False,
                "evidence_quality": "low",
                "sources_found": 0,
                "sources_usable": 0,
            },
        }

    current_id = save_assignment(student_text)
    if not current_id:
        return {
            "overall": 0.0,
            "semantic": 0.0,
            "paraphrase": 0.0,
            "style": 0.0,
            "decision": "NOT PLAGIARIZED",
            "used_fallback": True,
            "message": "Could not save input text to DB.",
            "services": {
                "paraphrase_api": get_paraphrase_base_url(),
                "wsa_api": get_wsa_base_url(),
                "semantic_api": get_semantic_base_url(),
            },
            "features": {"semantic": 0.0, "paraphrase": 0.0, "style": 0.0, "wsa_similarity": 0.0},
            "evidence": {"flags": ["db_save_failed"]},
            "prediction": {},
            "semantic_result": None,
            "paraphrase_result": None,
            "internet_result": [],
            "wsa_result": None,
            "internet_sources_count": 0,
            "source_status": {
                "score_reliable": False,
                "evidence_quality": "low",
                "sources_found": 0,
                "sources_usable": 0,
            },
        }

    previous = get_previous_assignment(current_id)
    if not previous:
        return {
            "overall": 0.0,
            "semantic": 0.0,
            "paraphrase": 0.0,
            "style": 0.0,
            "decision": "NOT PLAGIARIZED",
            "used_fallback": False,
            "message": "First submission saved. No previous DB records to compare yet.",
            "services": {
                "paraphrase_api": get_paraphrase_base_url(),
                "wsa_api": get_wsa_base_url(),
                "semantic_api": get_semantic_base_url(),
            },
            "features": {"semantic": 0.0, "paraphrase": 0.0, "style": 0.0, "wsa_similarity": 0.0},
            "evidence": {"flags": ["db_baseline_created"]},
            "prediction": {"decision": "NOT PLAGIARIZED"},
            "semantic_result": None,
            "paraphrase_result": None,
            "internet_result": [],
            "wsa_result": None,
            "internet_sources_count": 0,
            "source_status": {
                "score_reliable": False,
                "evidence_quality": "low",
                "sources_found": len(previous),
                "sources_usable": 0,
            },
            "db_mode": True,
            "matched_submission_id": None,
        }

    ranked = sorted(
        previous,
        key=lambda r: _overlap_ratio(student_text, r.get("text", "")),
        reverse=True,
    )[:3]

    best = None
    best_row = None
    for row in ranked:
        candidate = await _compare_single(student_text, row.get("text", ""))
        if best is None:
            best = candidate
            best_row = row
            continue

        # Prefer stronger DB decisions first, then higher score.
        candidate_rank = _decision_rank(candidate["decision"])
        best_rank = _decision_rank(best["decision"])
        if candidate_rank > best_rank:
            best = candidate
            best_row = row
        elif candidate_rank == best_rank and candidate["overall"] > best["overall"]:
            best = candidate
            best_row = row

    assert best is not None
    matched_id = int(best_row["id"]) if best_row else None

    return {
        "overall": best["overall"],
        "semantic": best["semantic"],
        "paraphrase": best["paraphrase"],
        "style": best["style"],
        "decision": best["decision"],
        "used_fallback": False,
        "message": "Compared against previous DB submissions (internet scan disabled).",
        "services": {
            "paraphrase_api": get_paraphrase_base_url(),
            "wsa_api": get_wsa_base_url(),
            "semantic_api": get_semantic_base_url(),
        },
        "features": {
            "semantic": best["semantic"],
            "paraphrase": best["paraphrase"],
            "db_text_overlap": best["lexical_overlap"],
            "style": best["style"],
            "wsa_similarity": best["wsa_similarity"],
            "display_style_similarity": best["wsa_similarity"],
            "display_style_change_ratio": best["style"],
        },
        "source_status": {
            "score_reliable": True,
            "evidence_quality": "high",
            "sources_found": len(previous),
            "sources_usable": len(ranked),
        },
        "evidence": {
            "coverage": 0.0,
            "best_lexical": best["lexical_overlap"],
            "db_text_overlap": best["lexical_overlap"],
            "best_semantic": best["semantic"],
            "best_paraphrase": best["paraphrase"],
            "style_similarity": best["wsa_similarity"],
            "hybrid_score": best["overall"],
            "flags": ["db_mode", best["evidence_flag"]],
        },
        "prediction": {
            "overall": best["overall"],
            "semantic": best["semantic"],
            "paraphrase": best["paraphrase"],
            "db_text_overlap": best["lexical_overlap"],
            "style": best["style"],
            "style_similarity": best["wsa_similarity"],
            "hybrid_score": best["overall"],
            "decision": best["decision"],
        },
        "semantic_result": best["semantic_result"],
        "paraphrase_result": best["paraphrase_result"],
        "internet_result": [],
        "wsa_result": best["wsa_result"],
        "internet_sources_count": 0,
        "db_mode": True,
        "matched_submission_id": matched_id,
    }
