import torch
from sentence_transformers import SentenceTransformer, util
from sinling import SinhalaTokenizer
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Internal Relative Imports for Lexical Analysis and Preprocessing
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text
from ..web_scraper import get_internet_resources, scrape_url_content

# --- DEVICE ACCELERATION CONFIGURATION ---
# Check for NVIDIA GPU presence to enable CUDA hardware acceleration.
# This can reduce processing time from 400s down to under 100s.
device = 'cuda' if torch.cuda.is_available() else 'cpu'

print(f"⏳ Loading LaBSE Model on: {device.upper()}...")
# Load the LaBSE model onto the detected device (GPU or CPU)
model = SentenceTransformer('sentence-transformers/LaBSE', device=device)
tokenizer = SinhalaTokenizer()
print(f"✅ Engine Ready using {device.upper()}.")

def split_sentences(text):
    """
    Splits input text into individual sentences based on the full stop (.).
    Only processes sentences longer than 10 characters to avoid noise.
    """
    if not text: return []
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    return sentences

def check_paraphrase_pair(source_sentence, student_sentence):
    """
    HYBRID DETECTION ENGINE:
    Calculates similarity using both Semantic (Meaning) and Lexical (Word-match) brains.
    Includes a 'Lexical Fallback' logic for high-level paraphrasing.
    """
    source_tokens = preprocess_text(source_sentence)
    student_tokens = preprocess_text(student_sentence)

    # 1. SMALL BRAIN (Lexical): Measures word-for-word overlap and synonym matching
    lex_ratio = calculate_lexical_similarity(source_tokens, student_tokens)
    lexical_score = round(lex_ratio * 100, 2)

    # 2. BIG BRAIN (Semantic): Uses LaBSE AI to calculate vector-based meaning similarity
    # Tensors are processed on GPU if available for maximum speed.
    emb1 = model.encode(source_sentence, convert_to_tensor=True)
    emb2 = model.encode(student_sentence, convert_to_tensor=True)
    cosine_score = util.pytorch_cos_sim(emb1, emb2)
    semantic_score = round(cosine_score.item() * 100, 2)

    # 3. CONDITIONAL WEIGHTING (Dynamic Mode Switching):
    # If Lexical match is very low (<40%), the student has likely transformed the text heavily.
    # In this case, we rely 100% on the Semantic AI brain to detect the theft.
    if lexical_score < 40:
        final_score = semantic_score
        mode = "Semantic-Only"
    else:
        # Standard Weighted Hybrid: 70% Semantic + 30% Lexical
        final_score = (semantic_score * 0.7) + (lexical_score * 0.3)
        mode = "Hybrid"
    
    return {
        "paraphrase_score": round(final_score, 2),
        "semantic_score": semantic_score,
        "lexical_score": lexical_score,
        "detection_mode": mode
    }

def process_single_url(url, input_sentences):
    """
    PARALLEL WORKER: Processes a single website against all input sentences.
    Limits scan to the top 100 sentences per page for performance optimization.
    """
    try:
        web_raw_content = scrape_url_content(url)
        if not web_raw_content: return None
            
        # Analyze only the top 100 sentences to ensure speed and relevance
        web_sentences = split_sentences(web_raw_content)[:100] 
        plagiarized_sentences = []
        
        for s_sent in input_sentences:
            best_match_score = 0
            best_analysis = {}
            
            for w_sent in web_sentences:
                analysis = check_paraphrase_pair(w_sent, s_sent)
                
                # DIAGNOSTIC LOGGING: Prints 'Near Matches' (>50%) to the server console.
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
            
            # ACCURACY THRESHOLD: Only record as plagiarism if total score >= 70%.
            if best_match_score >= 70:
                plagiarized_sentences.append(best_analysis)

        # FINAL SCORE (Equation 7): Percentage of plagiarized sentences in the input
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
    if not input_sentences: return {"error": "Input text too short."}

    # Step 1: Discovery Layer (Generating search queries from tokens)
    all_search_tokens = []
    for sentence in input_sentences:
        tokens = preprocess_text(sentence)
        all_search_tokens.extend([t for t in tokens if len(t) > 2])
    
    unique_tokens = list(dict.fromkeys(all_search_tokens))
    search_query = " ".join(unique_tokens[:10]) 

    print(f"📡 Multi-threaded Search Discovery: {search_query}")
    candidate_urls = get_internet_resources(search_query, num_results=7)
    
    url_reports = []
    # Step 2: Detection Layer (Executing 7 threads in parallel for speed).
    with ThreadPoolExecutor(max_workers=7) as executor:
        future_tasks = [executor.submit(process_single_url, url, input_sentences) for url in candidate_urls]
        for future in future_tasks:
            result = future.result()
            if result: url_reports.append(result)

    # Sort results to show the source with the highest plagiarism percentage first
    url_reports.sort(key=lambda x: x['overall_paraphrase_percentage'], reverse=True)
    return url_reports