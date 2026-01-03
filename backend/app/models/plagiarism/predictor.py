
import os
import re
import joblib
import numpy as np
import pandas as pd

from app.models.plagiarism.similarity import (
    semantic_similarity,
    paraphrase_similarity,
    style_similarity
)

# ---------------------------------
# Load trained regression model
# ---------------------------------
MODEL_PATH = "app/models/plagiarism/plagiarism_logreg_model.pkl"
model = joblib.load(MODEL_PATH)

# ---------------------------------
# Load reference corpus (ONCE)
# ---------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/models
CORPUS_PATH = os.path.join(
    os.path.dirname(BASE_DIR),   # app/
    "data",
    "corpus_sources.csv"
)

if not os.path.exists(CORPUS_PATH):
    raise FileNotFoundError(f"Corpus file not found: {CORPUS_PATH}")

corpus_df = pd.read_csv(CORPUS_PATH)
CORPUS_SOURCES = corpus_df["Source"].dropna().astype(str).tolist()

def split_sentences(text: str):
    return [
        s.strip()
        for s in re.split(r"[.!?।]", text)
        if len(s.strip()) > 10
    ]


def predict_plagiarism_from_text(text: str):
    """
    Predict plagiarism scores by comparing uploaded text
    against a reference corpus
    """

    suspicious_sentences = split_sentences(text)

    if not suspicious_sentences:
        return {
            "overall": 0.0,
            "semantic": 0.0,
            "paraphrase": 0.0,
            "style": 0.0,
            "decision": "NOT PLAGIARIZED"
        }

    sem_scores, para_scores, style_scores = [], [], []

    for sent in suspicious_sentences[:20]:   # limit for speed
        best_sem, best_para, best_style = 0.0, 0.0, 0.0

        for src in CORPUS_SOURCES[:200]:      # limit corpus size
            sem = semantic_similarity(sent, src)
            para = paraphrase_similarity(sent, src)
            sty = style_similarity(sent, src)

            if sem > best_sem:
                best_sem, best_para, best_style = sem, para, sty

        sem_scores.append(best_sem)
        para_scores.append(best_para)
        style_scores.append(best_style)

    semantic = float(np.mean(sem_scores))
    paraphrase = float(np.mean(para_scores))
    style = float(np.mean(style_scores))

    X = np.array([[semantic, paraphrase, style]])
    prob = model.predict_proba(X)[0][1]

    return {
        "overall": round(prob * 100, 2),
        "semantic": round(semantic, 2),
        "paraphrase": round(paraphrase, 2),
        "style": round(style, 2),
        "decision": "PLAGIARIZED" if prob >= 0.7 else "NOT PLAGIARIZED"
    }





















