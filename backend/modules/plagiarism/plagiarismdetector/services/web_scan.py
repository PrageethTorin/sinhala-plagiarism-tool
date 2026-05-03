import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ...parapahsedetection.modules.ParaphraseDetection.lexical_analyzer import (
    calculate_lexical_similarity,
    get_synonyms_from_db,
)
from ...parapahsedetection.modules.ParaphraseDetection.preprocessor import preprocess_text
from ...parapahsedetection.modules.web_scraper import (
    get_internet_resources,
    scrape_url_content,
)

try:
    _MODEL = SentenceTransformer("sentence-transformers/LaBSE")
except Exception:
    _MODEL = None


def _env_int(name, default, minimum=1):
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _env_float(name, default, minimum=0.0, maximum=1.0):
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, value))


FAST_WEB_SCAN = os.getenv("FAST_WEB_SCAN", "1").strip().lower() not in {"0", "false", "no"}
WEB_SCAN_MAX_QUERIES = _env_int("WEB_SCAN_MAX_QUERIES", 3 if FAST_WEB_SCAN else 5)
WEB_SCAN_MAX_QUERY_LENGTH = _env_int("WEB_SCAN_MAX_QUERY_LENGTH", 140 if FAST_WEB_SCAN else 180)
WEB_SCAN_MAX_URLS_LONG = _env_int("WEB_SCAN_MAX_URLS_LONG", 5 if FAST_WEB_SCAN else 10)
WEB_SCAN_MAX_URLS_SHORT = _env_int("WEB_SCAN_MAX_URLS_SHORT", 4 if FAST_WEB_SCAN else 6)
WEB_SCAN_RESULTS_LONG = _env_int("WEB_SCAN_RESULTS_LONG", 4 if FAST_WEB_SCAN else 6)
WEB_SCAN_RESULTS_SHORT = _env_int("WEB_SCAN_RESULTS_SHORT", 3 if FAST_WEB_SCAN else 4)
WEB_SCAN_MAX_WEB_SENTENCES = _env_int("WEB_SCAN_MAX_WEB_SENTENCES", 120 if FAST_WEB_SCAN else 240)
WEB_SCAN_MAX_CANDIDATES = _env_int("WEB_SCAN_MAX_CANDIDATES", 30 if FAST_WEB_SCAN else 60)
WEB_SCAN_MAX_WORKERS = _env_int("WEB_SCAN_MAX_WORKERS", 3 if FAST_WEB_SCAN else 4)
DIRECT_MATCH_MIN_CHARS = _env_int("WEB_SCAN_DIRECT_MATCH_MIN_CHARS", 24)
DIRECT_SHINGLE_THRESHOLD = _env_int("WEB_SCAN_DIRECT_SHINGLE_THRESHOLD", 65)
DIRECT_EARLY_DENSITY = _env_float("WEB_SCAN_DIRECT_EARLY_DENSITY", 0.75)


def split_sentences(text):
    if not text:
        return []

    return [
        s.strip()
        for s in re.split(r"[.!?।॥\n]+", text)
        if len(s.strip()) > 8
    ]


def pick_search_queries(text, max_queries=5, max_len=180):
    sentences = split_sentences(text)
    if not sentences:
        cleaned = " ".join(text.split()).strip()
        return [cleaned[:max_len]] if cleaned else []

    ranked = sorted(
        sentences,
        key=lambda s: (len(set(s.split())), len(s)),
        reverse=True,
    )

    queries = []
    first_sentence = sentences[0][:max_len]
    if first_sentence:
        queries.append(first_sentence)
        queries.append(f"\"{first_sentence}\"")

    for sentence in ranked:
        q = sentence[:max_len]
        if q and q not in queries:
            queries.append(q)
        if len(queries) >= max_queries:
            break

    return queries[:max_queries]


def _merge_scores(semantic_score, lexical_score):
    if lexical_score > 88:
        final_score = max(semantic_score, lexical_score)
        mode = "High-Lexical"
    else:
        final_score = (semantic_score * 0.82) + (lexical_score * 0.18)
        mode = "Hybrid"

    return {
        "paraphrase_score": round(final_score, 2),
        "semantic_score": round(float(semantic_score), 2),
        "lexical_score": round(float(lexical_score), 2),
        "detection_mode": mode,
    }


def _jaccard_tokens(tokens1, tokens2):
    if not tokens1 or not tokens2:
        return 0.0
    s1 = set(tokens1)
    s2 = set(tokens2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def _normalize_exact(text):
    value = unicodedata.normalize("NFC", str(text or "")).casefold()
    value = re.sub(r"[\u200b-\u200f\ufeff]", "", value)
    cleaned = []
    for char in value:
        category = unicodedata.category(char)
        cleaned.append(" " if category[0] in {"P", "S"} else char)
    return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def _copy_coverage_score(sentence, normalized_page):
    normalized_sentence = _normalize_exact(sentence)
    if len(normalized_sentence) < DIRECT_MATCH_MIN_CHARS or not normalized_page:
        return 0.0

    if normalized_sentence in normalized_page:
        return 100.0

    tokens = normalized_sentence.split()
    if len(tokens) < 4:
        return 0.0

    shingle_size = 5 if len(tokens) >= 8 else max(2, len(tokens) // 2)
    shingles = [
        " ".join(tokens[i : i + shingle_size])
        for i in range(0, len(tokens) - shingle_size + 1)
    ]
    if not shingles:
        return 0.0

    hits = sum(1 for shingle in shingles if shingle in normalized_page)
    return round((hits / len(shingles)) * 100.0, 2)


def _domain_rank(url: str) -> int:
    ul = (url or "").lower()
    if "si.wikipedia.org" in ul:
        return 0
    if ".gov.lk" in ul:
        return 1
    if ".ac.lk" in ul or ".edu" in ul:
        return 2
    if "groups.google.com" in ul or "huggingface.co/datasets" in ul:
        return 9
    return 5


def _is_wikipedia(url: str) -> bool:
    return "si.wikipedia.org/wiki/" in (url or "").lower()


def _make_direct_match(sentence, score=100.0):
    score = round(float(score), 2)
    return {
        "student_sentence": sentence,
        "source_sentence": sentence,
        "paraphrase_score": score,
        "semantic_score": score,
        "lexical_score": score,
        "mode": "High-Lexical",
        "aligned_words": [],
    }


def _normalize_token(token: str) -> str:
    return re.sub(r"^[^\w\u0D80-\u0DFF]+|[^\w\u0D80-\u0DFF]+$", "", token or "").strip().lower()


def _tokenize_preserve_spaces(text: str):
    if not text:
        return []
    return re.findall(r"\S+\s*", text, flags=re.UNICODE)


def _align_words(student_sentence: str, source_sentence: str):
    tokens = _tokenize_preserve_spaces(student_sentence)
    source_tokens = [_normalize_token(t) for t in _tokenize_preserve_spaces(source_sentence)]
    source_set = {t for t in source_tokens if t}

    aligned = []
    for idx, token in enumerate(tokens):
        norm = _normalize_token(token)
        if not norm:
            aligned.append({"token_index": idx, "match_type": "none"})
            continue

        if norm in source_set:
            aligned.append({"token_index": idx, "match_type": "exact"})
            continue

        synonyms = get_synonyms_from_db(norm)
        if synonyms and any(syn in source_set for syn in synonyms):
            aligned.append({"token_index": idx, "match_type": "synonym"})
        else:
            aligned.append({"token_index": idx, "match_type": "none"})

    return aligned


def _check_paraphrase(source_text, suspicious_text):
    source_tokens = preprocess_text(source_text)
    suspicious_tokens = preprocess_text(suspicious_text)

    lexical_ratio = calculate_lexical_similarity(source_tokens, suspicious_tokens)
    lexical_score = round(lexical_ratio * 100, 2)

    semantic_score = 0.0
    if _MODEL is not None:
        embeddings1 = _MODEL.encode(source_text, convert_to_tensor=True)
        embeddings2 = _MODEL.encode(suspicious_text, convert_to_tensor=True)
        cosine_score = util.pytorch_cos_sim(embeddings1, embeddings2)
        semantic_score = round(cosine_score.item() * 100, 2)
    else:
        try:
            tfidf = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))
            mat = tfidf.fit_transform([source_text, suspicious_text])
            semantic_score = round(float(cosine_similarity(mat[0], mat[1])[0][0]) * 100, 2)
        except Exception:
            semantic_score = lexical_score

    return _merge_scores(semantic_score, lexical_score)


def process_single_url(url, input_sentences):
    try:
        is_wiki = _is_wikipedia(url)
        web_raw_content = scrape_url_content(url)
        if not web_raw_content:
            return {
                "url": url,
                "overall_paraphrase_percentage": 0.0,
                "plagiarized_count": 0,
                "total_sentences": len(input_sentences),
                "detailed_matches": [],
                "source_found": True,
                "content_extracted": False,
            }

        max_web_sentences = WEB_SCAN_MAX_WEB_SENTENCES * (3 if is_wiki else 1)
        web_sentences = split_sentences(web_raw_content)[:max_web_sentences]
        if not web_sentences:
            return None

        detailed_matches = []
        best_scores = []
        normalized_page = _normalize_exact(web_raw_content)
        direct_match_by_index = {}
        full_text_direct_score = _copy_coverage_score(" ".join(input_sentences), normalized_page)
        full_text_threshold = max(30, DIRECT_SHINGLE_THRESHOLD - (10 if is_wiki else 0))
        if full_text_direct_score >= full_text_threshold:
            direct_score = max(90.0 if is_wiki else 85.0, full_text_direct_score)
            direct_match_by_index = {
                i: {
                    **_make_direct_match(s_sent, direct_score),
                    "aligned_words": _align_words(s_sent, s_sent),
                }
                for i, s_sent in enumerate(input_sentences)
            }

        if not direct_match_by_index:
            for i, s_sent in enumerate(input_sentences):
                direct_score = _copy_coverage_score(s_sent, normalized_page)
                if direct_score >= DIRECT_SHINGLE_THRESHOLD:
                    direct_match_by_index[i] = {
                        **_make_direct_match(
                            s_sent,
                            max(90.0 if is_wiki else 85.0, direct_score),
                        ),
                        "aligned_words": _align_words(s_sent, s_sent),
                    }

        direct_density = len(direct_match_by_index) / len(input_sentences) if input_sentences else 0.0
        if direct_match_by_index and (
            direct_density >= DIRECT_EARLY_DENSITY or (is_wiki and direct_density >= 0.3)
        ):
            for i, s_sent in enumerate(input_sentences):
                best_scores.append(
                    float(direct_match_by_index[i]["paraphrase_score"])
                    if i in direct_match_by_index
                    else 0.0
                )
            overall_direct = round(max(full_text_direct_score, direct_density * 100.0), 2)
            detailed_matches = list(direct_match_by_index.values())
            return {
                "url": url,
                "overall_paraphrase_percentage": max(
                    round(sum(best_scores) / len(best_scores), 2),
                    overall_direct,
                    90.0 if is_wiki else 0.0,
                ),
                "plagiarized_count": len(direct_match_by_index),
                "strong_matches": len(direct_match_by_index),
                "exact_or_near_matches": len(direct_match_by_index),
                "match_density": round(direct_density, 4),
                "exact_density": round(direct_density, 4),
                "total_sentences": len(input_sentences),
                "detailed_matches": detailed_matches[:25],
                "source_found": True,
                "content_extracted": True,
            }

        remaining_indexes = [
            i for i in range(len(input_sentences))
            if i not in direct_match_by_index
        ]
        input_tokens = [preprocess_text(s) for s in input_sentences]
        web_tokens = [preprocess_text(s) for s in web_sentences]
        semantic_rows = {}

        semantic_matrix = None
        if _MODEL is not None and remaining_indexes:
            try:
                remaining_sentences = [input_sentences[i] for i in remaining_indexes]
                input_embeddings = _MODEL.encode(remaining_sentences, convert_to_tensor=True)
                web_embeddings = _MODEL.encode(web_sentences, convert_to_tensor=True)
                semantic_matrix = util.pytorch_cos_sim(input_embeddings, web_embeddings).cpu().numpy() * 100.0
                semantic_rows = {sentence_index: row for row, sentence_index in enumerate(remaining_indexes)}
            except Exception:
                semantic_matrix = None

        for i, s_sent in enumerate(input_sentences):
            if i in direct_match_by_index:
                best_scores.append(100.0)
                detailed_matches.append(direct_match_by_index[i])
                continue

            best_match_score = 0.0
            best_analysis = None

            ranked_candidates = sorted(
                range(len(web_sentences)),
                key=lambda j: _jaccard_tokens(input_tokens[i], web_tokens[j]),
                reverse=True,
            )[:WEB_SCAN_MAX_CANDIDATES]

            for j in ranked_candidates:
                w_sent = web_sentences[j]
                lexical_score = round(
                    calculate_lexical_similarity(web_tokens[j], input_tokens[i]) * 100, 2
                )

                if semantic_matrix is not None and i in semantic_rows:
                    semantic_score = float(semantic_matrix[semantic_rows[i]][j])
                else:
                    semantic_score = lexical_score

                analysis = _merge_scores(semantic_score, lexical_score)
                if analysis["paraphrase_score"] > best_match_score:
                    best_match_score = analysis["paraphrase_score"]
                    best_analysis = {
                        "student_sentence": s_sent,
                        "source_sentence": w_sent,
                        "paraphrase_score": analysis["paraphrase_score"],
                        "semantic_score": analysis["semantic_score"],
                        "lexical_score": analysis["lexical_score"],
                        "mode": analysis["detection_mode"],
                        "aligned_words": _align_words(s_sent, w_sent),
                    }

            best_scores.append(best_match_score)

            if best_analysis and best_match_score >= 45:
                detailed_matches.append(best_analysis)

        overall_score = (sum(best_scores) / len(best_scores)) if best_scores else 0.0
        plagiarized_count = sum(1 for s in best_scores if s >= 55)
        strong_matches = sum(1 for s in best_scores if s >= 75)
        exact_or_near = sum(1 for s in best_scores if s >= 90)
        match_density = (strong_matches / len(input_sentences)) if input_sentences else 0.0
        exact_density = (exact_or_near / len(input_sentences)) if input_sentences else 0.0
        detailed_matches.sort(key=lambda x: x["paraphrase_score"], reverse=True)

        return {
            "url": url,
            "overall_paraphrase_percentage": round(overall_score, 2),
            "plagiarized_count": plagiarized_count,
            "strong_matches": strong_matches,
            "exact_or_near_matches": exact_or_near,
            "match_density": round(match_density, 4),
            "exact_density": round(exact_density, 4),
            "total_sentences": len(input_sentences),
            "detailed_matches": detailed_matches[:25],
            "source_found": True,
            "content_extracted": True,
        }

    except Exception:
        return None


def check_internet_plagiarism(student_text):
    input_sentences = split_sentences(student_text)
    if not input_sentences:
        return {"error": "Input text too short."}

    search_queries = pick_search_queries(
        student_text,
        max_queries=WEB_SCAN_MAX_QUERIES,
        max_len=WEB_SCAN_MAX_QUERY_LENGTH,
    )

    candidate_urls = []
    seen = set()
    max_urls = WEB_SCAN_MAX_URLS_LONG if len(input_sentences) > 3 else WEB_SCAN_MAX_URLS_SHORT
    per_query_results = WEB_SCAN_RESULTS_LONG if len(input_sentences) > 3 else WEB_SCAN_RESULTS_SHORT

    for query in search_queries[:2]:
        wiki_query = f"site:si.wikipedia.org \"{query}\""
        wiki_urls = get_internet_resources(wiki_query, num_results=3)
        for url in wiki_urls:
            if _is_wikipedia(url) and url not in seen:
                seen.add(url)
                candidate_urls.append(url)
            if len(candidate_urls) >= max_urls:
                break
        if len(candidate_urls) >= max_urls:
            break

    for query in search_queries:
        urls = get_internet_resources(query, num_results=per_query_results)
        for url in urls:
            if url not in seen:
                seen.add(url)
                candidate_urls.append(url)
            if len(candidate_urls) >= max_urls:
                break
        if len(candidate_urls) >= max_urls:
            break

    if not candidate_urls:
        return []

    url_reports = []

    with ThreadPoolExecutor(max_workers=WEB_SCAN_MAX_WORKERS) as executor:
        future_tasks = {
            executor.submit(process_single_url, url, input_sentences): url
            for url in candidate_urls
        }

        for future in as_completed(future_tasks):
            result = future.result()
            if result is not None:
                url_reports.append(result)

                if result.get("overall_paraphrase_percentage", 0) >= 92 and result.get("exact_density", 0) >= 0.5:
                    break

    url_reports.sort(
        key=lambda x: (
            float(x.get("overall_paraphrase_percentage", 0.0)),
            float(x.get("exact_density", 0.0)),
            float(x.get("match_density", 0.0)),
            -_domain_rank(x.get("url", "")),
        ),
        reverse=True,
    )

    wiki_strong = [
        r
        for r in url_reports
        if _is_wikipedia(r.get("url", ""))
        and float(r.get("overall_paraphrase_percentage", 0.0)) >= 70.0
    ]
    if wiki_strong:
        best_wiki = max(
            wiki_strong,
            key=lambda x: (
                float(x.get("overall_paraphrase_percentage", 0.0)),
                float(x.get("exact_density", 0.0)),
                float(x.get("match_density", 0.0)),
            ),
        )
        url_reports = [best_wiki] + [r for r in url_reports if r is not best_wiki]

    return url_reports[:3]
