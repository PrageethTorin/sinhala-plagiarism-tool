# backend/modules/ParaphraseDetection/plagiarism_engine.py

import torch
from sentence_transformers import SentenceTransformer, util
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text
from concurrent.futures import ThreadPoolExecutor
from ..web_scraper import get_internet_resources, scrape_url_content

# 1. Load the Big Brain (LaBSE) once when server starts
print("⏳ Loading AI Model (LaBSE)... This might take a minute...")
model = SentenceTransformer('sentence-transformers/LaBSE')
print("✅ AI Model Loaded Successfully!")

def split_sentences(text):
    """
    Lightweight sentence splitter used by the engine.
    Splits on full stops and returns sentences longer than 10 chars.
    (Keeps behaviour compatible with earlier versions.)
    """
    if not text:
        return []
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    return sentences

def check_paraphrase(source_text, suspicious_text):
    """
    Hybrid Detection: Combines LaBSE (Semantic) and Custom SQL (Lexical).
    """
    
    # --- STEP 1: PREPROCESSING ---
    source_tokens = preprocess_text(source_text)
    suspicious_tokens = preprocess_text(suspicious_text)

    # --- STEP 2: SMALL BRAIN (Lexical Analysis) ---
    lexical_ratio = calculate_lexical_similarity(source_tokens, suspicious_tokens)
    lexical_score = round(lexical_ratio * 100, 2)

    # --- STEP 3: BIG BRAIN (Semantic Analysis) ---
    embeddings1 = model.encode(source_text, convert_to_tensor=True)
    embeddings2 = model.encode(suspicious_text, convert_to_tensor=True)
    
    cosine_score = util.pytorch_cos_sim(embeddings1, embeddings2)
    semantic_score = round(cosine_score.item() * 100, 2)

    # --- STEP 4: THE COMBINED SCORE ---
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
    PARALLEL WORKER: Processes a single website against all input sentences.
    """
    try:
        web_raw_content = scrape_url_content(url)
        if not web_raw_content:
            return None
            
        web_sentences = split_sentences(web_raw_content)[:100]
        plagiarized_sentences = []
        
        for s_sent in input_sentences:
            best_match_score = 0
            best_analysis = {}
            
            for w_sent in web_sentences:
                analysis = check_paraphrase(w_sent, s_sent)
                
                if analysis["paraphrase_score"] > 50:
                    print(f"🔍 Near Match at {url[:25]}... [{analysis['detection_mode']}]")
                    print(f"   Score: {analysis['paraphrase_score']}% (Sem: {analysis['semantic_score']} | Lex: {analysis['lexical_score']})")

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
            
            if best_match_score >= 70:
                plagiarized_sentences.append(best_analysis)

        overall_score = (len(plagiarized_sentences) / len(input_sentences)) * 100

        return {
            "url": url,
            "overall_paraphrase_percentage": round(overall_score, 2),
            "plagiarized_count": len(plagiarized_sentences),
            "total_sentences": len(input_sentences),
            "detailed_matches": plagiarized_sentences
        }

    except Exception as e:
        print(f"⚠️ Error processing {url}: {e}")
        return None


def check_internet_plagiarism(student_text):
    """
    MAIN WORKFLOW: Coordinates web discovery and multi-threaded sentence analysis.
    """
    input_sentences = split_sentences(student_text)
    if not input_sentences:
        return {"error": "Input text too short."}

    all_search_tokens = []
    for sentence in input_sentences:
        tokens = preprocess_text(sentence)
        all_search_tokens.extend([t for t in tokens if len(t) > 2])
    
    unique_tokens = list(dict.fromkeys(all_search_tokens))
    search_query = " ".join(unique_tokens[:10]) 

    print(f"📡 Multi-threaded Search Discovery: {search_query}")
    candidate_urls = get_internet_resources(search_query, num_results=7)
    
    url_reports = []

    with ThreadPoolExecutor(max_workers=7) as executor:
        future_tasks = [
            executor.submit(process_single_url, url, input_sentences)
            for url in candidate_urls
        ]
        for future in future_tasks:
            result = future.result()
            if result:
                url_reports.append(result)

    url_reports.sort(
        key=lambda x: x['overall_paraphrase_percentage'],
        reverse=True
    )

    return url_reports