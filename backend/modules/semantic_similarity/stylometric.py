# backend/semantic_similarity/stylometric.py
from .utils import split_sentences_simple

def stylometric_similarity(a: str, b: str) -> float:
    sents_a = split_sentences_simple(a)
    sents_b = split_sentences_simple(b)
    if not sents_a or not sents_b:
        return 0.0
    avg_a = sum(len(s.split()) for s in sents_a) / max(1, len(sents_a))
    avg_b = sum(len(s.split()) for s in sents_b) / max(1, len(sents_b))
    styl_score = max(0.0, 1.0 - abs(avg_a - avg_b) / max(avg_a, avg_b, 1.0))
    return styl_score
