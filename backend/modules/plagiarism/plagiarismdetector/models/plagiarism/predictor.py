
import os
import re
import csv
import joblib
import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(_THIS_DIR, "plagiarism_logreg_model.pkl")
model = joblib.load(MODEL_PATH)

_PLAGIARISMDETECTOR_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
CORPUS_PATH = os.path.join(_PLAGIARISMDETECTOR_DIR, "data", "score_dataset.csv")

if not os.path.exists(CORPUS_PATH):
    raise FileNotFoundError(f"Corpus file not found: {CORPUS_PATH}")

CORPUS_SOURCES = []
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        val = (row.get("Source") or "").strip()
        if val:
            CORPUS_SOURCES.append(val)


def split_sentences(text: str):
    return [
        s.strip()
        for s in re.split(r"[.!?।]", text)
        if len(s.strip()) > 10
    ]


def _paraphrase_similarity(a: str, b: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))
    try:
        tfidf = vectorizer.fit_transform([a, b])
        sim = cosine_similarity(tfidf[0], tfidf[1])[0][0]
        return float(sim * 100)
    except Exception:
        return 0.0


def _style_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ratio = min(len(a), len(b)) / max(len(a), len(b))
    return float(ratio * 100)


def _hybrid_decision(semantic: float, paraphrase: float, style_change: float):
    style_similarity = 100.0 - style_change

    hybrid_score = (
        0.45 * semantic +
        0.40 * paraphrase +
        0.15 * style_similarity
    )

    if semantic >= 85 and paraphrase >= 70:
        decision = "PLAGIARIZED"
        overall = max(hybrid_score, 80.0)
    elif hybrid_score >= 75:
        decision = "PLAGIARIZED"
        overall = hybrid_score
    elif hybrid_score >= 55:
        decision = "SUSPICIOUS"
        overall = hybrid_score
    else:
        decision = "NOT PLAGIARIZED"
        overall = min(hybrid_score, 54.99)

    return round(style_similarity, 2), round(hybrid_score, 2), round(overall, 2), decision


def predict_plagiarism_from_text(text: str):
    suspicious_sentences = split_sentences(text)

    if not suspicious_sentences:
        return {
            "overall": 0.0,
            "semantic": 0.0,
            "paraphrase": 0.0,
            "style": 0.0,
            "style_similarity": 100.0,
            "hybrid_score": 0.0,
            "decision": "NOT PLAGIARIZED"
        }

    sem_scores, para_scores, style_scores = [], [], []

    for sent in suspicious_sentences[:3]:
        best_para, best_style = 0.0, 0.0

        for src in CORPUS_SOURCES[:20]:
            para = _paraphrase_similarity(sent, src)
            sty = _style_similarity(sent, src)

            if para > best_para:
                best_para, best_style = para, sty

        semantic = best_para * 0.8

        sem_scores.append(semantic)
        para_scores.append(best_para)
        style_scores.append(100.0 - best_style)  # style change

    semantic = float(np.mean(sem_scores))
    paraphrase = float(np.mean(para_scores))
    style = float(np.mean(style_scores))

    X = pd.DataFrame([{
        "semantic": semantic,
        "paraphrase": paraphrase,
        "style": style,
    }])
    _ = float(model.predict_proba(X)[0][1])  # keep model used, but do not expose as final overall

    style_similarity, hybrid_score, overall, decision = _hybrid_decision(
        semantic=semantic,
        paraphrase=paraphrase,
        style_change=style,
    )

    return {
        "overall": overall,
        "semantic": round(semantic, 2),
        "paraphrase": round(paraphrase, 2),
        "style": round(style, 2),
        "style_similarity": style_similarity,
        "hybrid_score": hybrid_score,
        "decision": decision,
    }


def predict_plagiarism_from_features(semantic: float, paraphrase: float, style: float):
    semantic_v = float(semantic or 0.0)
    paraphrase_v = float(paraphrase or 0.0)
    style_v = float(style or 0.0)

    X = pd.DataFrame([{
        "semantic": semantic_v,
        "paraphrase": paraphrase_v,
        "style": style_v,
    }])
    _ = float(model.predict_proba(X)[0][1])  # keep model used, but do not expose as final overall

    style_similarity, hybrid_score, overall, decision = _hybrid_decision(
        semantic=semantic_v,
        paraphrase=paraphrase_v,
        style_change=style_v,
    )

    return {
        "overall": overall,
        "semantic": round(semantic_v, 2),
        "paraphrase": round(paraphrase_v, 2),
        "style": round(style_v, 2),
        "style_similarity": style_similarity,
        "hybrid_score": hybrid_score,
        "decision": decision,
    }