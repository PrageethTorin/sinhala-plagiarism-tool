import torch
import re
from sentence_transformers import SentenceTransformer, util
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..web_scraper import get_internet_resources, scrape_url_content

print("Loading AI Model (LaBSE)... This might take a minute...")
model = SentenceTransformer('sentence-transformers/LaBSE')
print("AI Model Loaded Successfully!")


def split_sentences(text):
    """
    Lightweight sentence splitter used by the engine.
    Handles Sinhala and English sentence boundaries.
    """
    if not text:
        return []

    sentences = [
        s.strip()
        for s in re.split(r"[.!?।॥\n]+", text)
        if len(s.strip()) > 8
    ]
    return sentences


def pick_search_queries(text, max_queries=3, max_len=140):
    """
    Pick the best short sentence-level search queries from long text.
    """
    sentences = split_sentences(text)
    if not sentences:
        cleaned = " ".join(text.split()).strip()
        return [cleaned[:max_len]] if cleaned else []

    ranked = sorted(
        sentences,
        key=lambda s: (len(set(s.split())), len(s)),
        reverse=True
    )

    queries = []
    first_sentence = sentences[0][:max_len]
    if first_sentence:
        queries.append(first_sentence)

    for sentence in ranked:
        q = sentence[:max_len]
        if q and q not in queries:
            queries.append(q)
        if len(queries) >= max_queries:
            break

    return queries[:max_queries]


def check_paraphrase(source_text, suspicious_text):
    """
    Hybrid Detection: Combines LaBSE (Semantic) and Custom SQL (Lexical).
    """
    source_tokens = preprocess_text(source_text)
    suspicious_tokens = preprocess_text(suspicious_text)

    lexical_ratio = calculate_lexical_similarity(source_tokens, suspicious_tokens)
    lexical_score = round(lexical_ratio * 100, 2)

    embeddings1 = model.encode(source_text, convert_to_tensor=True)
    embeddings2 = model.encode(suspicious_text, convert_to_tensor=True)

    cosine_score = util.pytorch_cos_sim(embeddings1, embeddings2)
    semantic_score = round(cosine_score.item() * 100, 2)

    if lexical_score > 80:
        final_score = max(semantic_score, lexical_score)
        mode = "High-Lexical"
    else:
        final_score = (semantic_score * 0.7) + (lexical_score * 0.3)
        mode = "Hybrid"

    final_score = round(final_score, 2)

    return {
        "paraphrase_score": final_score,
        "semantic_score": semantic_score,
        "lexical_score": lexical_score,
        "detection_mode": mode
    }


def process_single_url(url, input_sentences):
    """
    Process one website against all input sentences.
    """
    try:
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

        web_sentences = split_sentences(web_raw_content)[:120]
        if not web_sentences:
            return None

        detailed_matches = []
        best_scores = []

        for s_sent in input_sentences:
            best_match_score = 0.0
            best_analysis = None

            for w_sent in web_sentences:
                analysis = check_paraphrase(w_sent, s_sent)

                if analysis["paraphrase_score"] > best_match_score:
                    best_match_score = analysis["paraphrase_score"]
                    best_analysis = {
                        "student_sentence": s_sent,
                        "source_sentence": w_sent,
                        "paraphrase_score": analysis["paraphrase_score"],
                        "semantic_score": analysis["semantic_score"],
                        "lexical_score": analysis["lexical_score"],
                        "mode": analysis["detection_mode"]
                    }

            best_scores.append(best_match_score)

            if best_analysis and best_match_score >= 55:
                detailed_matches.append(best_analysis)

        overall_score = (sum(best_scores) / len(best_scores)) if best_scores else 0.0
        plagiarized_count = sum(1 for s in best_scores if s >= 60)
        detailed_matches.sort(key=lambda x: x["paraphrase_score"], reverse=True)

        return {
            "url": url,
            "overall_paraphrase_percentage": round(overall_score, 2),
            "plagiarized_count": plagiarized_count,
            "total_sentences": len(input_sentences),
            "detailed_matches": detailed_matches[:25],
            "source_found": True,
            "content_extracted": True,
        }

    except Exception as e:
        print(f"[WARN] Error processing {url}: {e}")
        return None


def check_internet_plagiarism(student_text):
    """
    Main workflow: web discovery + limited parallel processing.
    """
    input_sentences = split_sentences(student_text)
    if not input_sentences:
        return {"error": "Input text too short."}

    # NEW: use sentence-based search queries instead of token soup
    search_queries = pick_search_queries(student_text, max_queries=3, max_len=140)
    print(f"[DISCOVERY] Search queries: {search_queries}")

    candidate_urls = []
    seen = set()

    for query in search_queries:
        urls = get_internet_resources(query, num_results=3)
        for url in urls:
            if url not in seen:
                seen.add(url)
                candidate_urls.append(url)
            if len(candidate_urls) >= 3:
                break
        if len(candidate_urls) >= 3:
            break

    if not candidate_urls:
        return []

    url_reports = []

    # NEW: fewer workers for speed and stability
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_tasks = {
            executor.submit(process_single_url, url, input_sentences): url
            for url in candidate_urls
        }

        for future in as_completed(future_tasks):
            result = future.result()
            if result is not None:
                url_reports.append(result)

                # NEW: early stop if a strong result is already found
                if result.get("overall_paraphrase_percentage", 0) >= 85:
                    print(f"[EARLY STOP] Strong match found: {result.get('url')}")
                    break

    url_reports.sort(
        key=lambda x: x['overall_paraphrase_percentage'],
        reverse=True
    )

    return url_reports[:3]