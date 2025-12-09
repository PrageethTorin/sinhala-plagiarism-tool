# backend/semantic_similarity/lexical.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def lexical_similarity(a: str, b: str) -> float:
    try:
        tfidf = TfidfVectorizer().fit([a, b])
        vecs = tfidf.transform([a, b])
        sim = float(cosine_similarity(vecs[0], vecs[1])[0,0])
        return sim
    except Exception:
        return 0.0
