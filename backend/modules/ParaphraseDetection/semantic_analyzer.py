# modules/ParaphraseDetection/semantic_analyzer.py
from sentence_transformers import SentenceTransformer, util

# We load the AI model globally so it only loads ONCE when the server starts.
# 'LaBSE' is excellent for supporting 100+ languages including Sinhala.
print("⏳ Loading AI Model (LaBSE)... This might take a minute...")
model = SentenceTransformer('sentence-transformers/LaBSE')
print("✅ AI Model Loaded Successfully!")

def calculate_semantic_similarity(text1, text2):
    """
    Calculates how similar the MEANINGS of two sentences are.
    Returns a score between 0.0 (Different) and 1.0 (Same Meaning).
    """
    if not text1 or not text2:
        return 0.0

    # 1. Convert text into "Embeddings" (Number lists representing meaning)
    # convert_to_tensor=True helps us do math on them quickly
    embeddings1 = model.encode(text1, convert_to_tensor=True)
    embeddings2 = model.encode(text2, convert_to_tensor=True)

    # 2. Calculate Cosine Similarity
    # This checks how close the two meanings are in vector space
    score_tensor = util.pytorch_cos_sim(embeddings1, embeddings2)

    # Convert the complex tensor result into a simple Python number (float)
    semantic_score = score_tensor.item()
    
    return semantic_score