import torch
import re
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..web_scraper import get_internet_resources, scrape_url_content

print("Loading AI Model (LaBSE)... This might take a minute...")
try:
    model = SentenceTransformer("sentence-transformers/LaBSE")
    print("AI Model Loaded Successfully!")
except Exception as e:
    model = None
    print(f"[WARN] LaBSE model unavailable, using TF-IDF fallback semantic scoring: {e}")


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


def pick_search_queries(text, max_queries=5, max_len=180):
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
    # Prefer an exact-quote query for the first sentence to find the source page.
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


def check_paraphrase(source_text, suspicious_text):
    """
    Hybrid Detection: Combines LaBSE (Semantic) and Custom SQL (Lexical).
    """
    source_tokens = preprocess_text(source_text)
    suspicious_tokens = preprocess_text(suspicious_text)

    lexical_ratio = calculate_lexical_similarity(source_tokens, suspicious_tokens)
    lexical_score = round(lexical_ratio * 100, 2)

    semantic_score = 0.0
    if model is not None:
        embeddings1 = model.encode(source_text, convert_to_tensor=True)
        embeddings2 = model.encode(suspicious_text, convert_to_tensor=True)
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


def _merge_scores(semantic_score, lexical_score):
    if lexical_score > 88:
        final_score = max(semantic_score, lexical_score)
        mode = "High-Lexical"
    else:
        # Favor semantic meaning more for synonym-heavy paraphrases.
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

        web_sentences = split_sentences(web_raw_content)[:240]
        if not web_sentences:
            return None

        detailed_matches = []
        best_scores = []
        input_tokens = [preprocess_text(s) for s in input_sentences]
        web_tokens = [preprocess_text(s) for s in web_sentences]

        semantic_matrix = None
        if model is not None:
            try:
                input_embeddings = model.encode(input_sentences, convert_to_tensor=True)
                web_embeddings = model.encode(web_sentences, convert_to_tensor=True)
                semantic_matrix = util.pytorch_cos_sim(input_embeddings, web_embeddings).cpu().numpy() * 100.0
            except Exception as e:
                print(f"[WARN] Batch semantic scoring failed for {url}: {e}")
                semantic_matrix = None

        for i, s_sent in enumerate(input_sentences):
            best_match_score = 0.0
            best_analysis = None

            ranked_candidates = sorted(
                range(len(web_sentences)),
                key=lambda j: _jaccard_tokens(input_tokens[i], web_tokens[j]),
                reverse=True,
            )[:60]

            for j in ranked_candidates:
                w_sent = web_sentences[j]
                lexical_score = round(calculate_lexical_similarity(web_tokens[j], input_tokens[i]) * 100, 2)

                if semantic_matrix is not None:
                    semantic_score = float(semantic_matrix[i][j])
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
                        "mode": analysis["detection_mode"]
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
    search_queries = pick_search_queries(student_text, max_queries=5, max_len=180)
    print(f"[DISCOVERY] Search queries: {search_queries}")

    candidate_urls = []
    seen = set()
    max_urls = 10 if len(input_sentences) > 3 else 6
    per_query_results = 6 if len(input_sentences) > 3 else 4

    # 1) Wikipedia-first pass: check Sinhala Wikipedia sources before generic web.
    for query in search_queries[:2]:
        wiki_query = f'site:si.wikipedia.org "{query}"'
        wiki_urls = get_internet_resources(wiki_query, num_results=3)
        for url in wiki_urls:
            if _is_wikipedia(url) and url not in seen:
                seen.add(url)
                candidate_urls.append(url)
            if len(candidate_urls) >= max_urls:
                break
        if len(candidate_urls) >= max_urls:
            break

    # 2) Generic web pass
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

    # NEW: fewer workers for speed and stability
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_tasks = {
            executor.submit(process_single_url, url, input_sentences): url
            for url in candidate_urls
        }

        for future in as_completed(future_tasks):
            result = future.result()
            if result is not None:
                url_reports.append(result)

                # NEW: early stop if a strong result is already found
                if result.get("overall_paraphrase_percentage", 0) >= 92 and result.get("exact_density", 0) >= 0.5:
                    print(f"[EARLY STOP] Strong match found: {result.get('url')}")
                    break

    url_reports.sort(
        key=lambda x: (
            float(x.get("exact_density", 0.0)),
            float(x.get("match_density", 0.0)),
            float(x.get("overall_paraphrase_percentage", 0.0)),
            -_domain_rank(x.get("url", "")),
        ),
        reverse=True,
    )

    # If a strong Wikipedia source exists, force it to the top for final reporting.
    wiki_strong = [
        r for r in url_reports
        if _is_wikipedia(r.get("url", ""))
        and float(r.get("overall_paraphrase_percentage", 0.0)) >= 70.0
    ]
    if wiki_strong:
        best_wiki = max(
            wiki_strong,
            key=lambda x: (
                float(x.get("exact_density", 0.0)),
                float(x.get("match_density", 0.0)),
                float(x.get("overall_paraphrase_percentage", 0.0)),
            ),
        )
        url_reports = [best_wiki] + [r for r in url_reports if r is not best_wiki]

    return url_reports[:3]
