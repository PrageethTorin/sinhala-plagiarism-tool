# backend/modules/ParaphraseDetection/plagiarism_engine.py

import torch
from sentence_transformers import SentenceTransformer, util
from .lexical_analyzer import calculate_lexical_similarity
from .preprocessor import preprocess_text

# 1. Load the Big Brain (LaBSE) once when server starts
print("⏳ Loading AI Model (LaBSE)... This might take a minute...")
model = SentenceTransformer('sentence-transformers/LaBSE')
print("✅ AI Model Loaded Successfully!")

def check_paraphrase(source_text, suspicious_text):
    """
    Hybrid Detection: Combines LaBSE (Semantic) and Custom SQL (Lexical).
    """
    
    # --- STEP 1: PREPROCESSING ---
    # Clean the text (remove punctuation, stop words)
    source_tokens = preprocess_text(source_text)
    suspicious_tokens = preprocess_text(suspicious_text)

    # --- STEP 2: SMALL BRAIN (Lexical Analysis) ---
    # Checks for synonyms and exact word matches
    lexical_ratio = calculate_lexical_similarity(source_tokens, suspicious_tokens)
    lexical_score = round(lexical_ratio * 100, 2)

    # --- STEP 3: BIG BRAIN (Semantic Analysis) ---
    # Converts sentences to vectors and checks meaning
    embeddings1 = model.encode(source_text, convert_to_tensor=True)
    embeddings2 = model.encode(suspicious_text, convert_to_tensor=True)
    
    cosine_score = util.pytorch_cos_sim(embeddings1, embeddings2)
    semantic_score = round(cosine_score.item() * 100, 2)

    # --- STEP 4: THE COMBINED SCORE (The Industrial Formula) ---
    # We trust the AI (Big Brain) 70% and the Lexical (Small Brain) 30%
    # However, if Lexical is VERY high (Direct Copy), we force the score up.
    
    if lexical_score > 80:
        # If 80% of words are copied, it is DEFINITELY plagiarism.
        final_score = max(semantic_score, lexical_score)
    else:
        # Standard Weighted Average
        final_score = (semantic_score * 0.7) + (lexical_score * 0.3)
    
    final_score = round(final_score, 2)

    # --- STEP 5: THE VERDICT ---
    is_paraphrased = False
    if final_score >= 70:
        is_paraphrased = True  # High probability of plagiarism
    elif final_score >= 50:
        is_paraphrased = True  # Moderate/Suspicious

    return {
        "is_paraphrased": is_paraphrased,
        "paraphrase_score": final_score,   # The Combined Score
        "semantic_score": semantic_score,  # Big Brain Output
        "lexical_score": lexical_score     # Mini Brain Output
    }