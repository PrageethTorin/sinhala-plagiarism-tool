import torch
from sentence_transformers import SentenceTransformer, util
from sinling import SinhalaTokenizer
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Internal Relative Imports
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text
from ..web_scraper import get_internet_resources, scrape_url_content

# --- DEVICE ACCELERATION ---
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"⏳ Loading LaBSE Model on: {device.upper()}...")
model = SentenceTransformer('sentence-transformers/LaBSE', device=device)
tokenizer = SinhalaTokenizer()
print(f"✅ Engine Ready using {device.upper()}.")

def split_sentences(text):
    if not text: return []
    # Splits at full stops; ignores noise sentences shorter than 10 characters
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    return sentences

def check_paraphrase_pair(source_sentence, student_sentence):
    """
    Hybrid Logic: 70% Semantic + 30% Lexical.
    Switches to 100% Semantic if word-overlap (Lexical) is below 40%.
    """
    source_tokens = preprocess_text(source_sentence)
    student_tokens = preprocess_text(student_sentence)

    # 1. Lexical Score
    lex_ratio = calculate_lexical_similarity(source_tokens, student_tokens)
    lexical_score = round(lex_ratio * 100, 2)

    # 2. Semantic Score (LaBSE)
    emb1 = model.encode(source_sentence, convert_to_tensor=True)
    emb2 = model.encode(student_sentence, convert_to_tensor=True)
    cosine_score = util.pytorch_cos_sim(emb1, emb2)
    semantic_score = round(cosine_score.item() * 100, 2)

    # 3. Mode Selection
    if lexical_score < 40:
        final_score = semantic_score
        mode = "Semantic-Only"
    else:
        final_score = (semantic_score * 0.7) + (lexical_score * 0.3)
        mode = "Hybrid"
    
    return {
        "paraphrase_score": round(final_score, 2),
        "semantic_score": semantic_score,
        "lexical_score": lexical_score,
        "detection_mode": mode
    }

def process_single_url(url, input_sentences):
    try:
        web_raw_content = scrape_url_content(url)
        if not web_raw_content: return None
            
        web_sentences = split_sentences(web_raw_content)[:100] 
        plagiarized_sentences = []
        
        for s_sent in input_sentences:
            best_match_score = 0
            best_analysis = {}
            
            for w_sent in web_sentences:
                analysis = check_paraphrase_pair(w_sent, s_sent)
                
                # Diagnostic log for threshold monitoring
                if analysis["paraphrase_score"] > 50: 
                    print(f"🔍 Match Found: {url[:30]}... [{analysis['detection_mode']}] Score: {analysis['paraphrase_score']}%")

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
            
            # Record only if it crosses the 50% "Plagiarism Gap"
            if best_match_score > 50:
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
    input_sentences = split_sentences(student_text)
    if not input_sentences: return {"error": "Input text too short."}

    # Keyword Priority Extraction (Longest unique tokens)
    all_tokens = []
    for sent in input_sentences:
        tokens = [t for t in preprocess_text(sent) if len(t) > 3]
        all_tokens.extend(tokens)
    
    unique_tokens = list(set(all_tokens))
    unique_tokens.sort(key=len, reverse=True) 
    search_query = " ".join(unique_tokens[:12]) 

    print(f"📡 Discovery Query: {search_query}")
    candidate_urls = get_internet_resources(search_query, num_results=10)
    
    url_reports = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_tasks = [executor.submit(process_single_url, url, input_sentences) for url in candidate_urls]
        for future in future_tasks:
            result = future.result()
            if result: url_reports.append(result)

    url_reports.sort(key=lambda x: x['overall_paraphrase_percentage'], reverse=True)
    return url_reports