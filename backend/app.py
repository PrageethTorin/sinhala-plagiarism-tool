# backend/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Config ---
MODEL_NAME = "sentence-transformers/LaBSE"   # good multilingual model
# Load model once (takes time on first run)
model = SentenceTransformer(MODEL_NAME)

app = FastAPI(title="Sinhala Similarity API")

# allow requests from your frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body models
class Pair(BaseModel):
    a: str
    b: str

class MultiDocs(BaseModel):
    doc_text: str
    corpus: list[str]  # list of strings to compare against

# Simple health endpoint
@app.get("/ping")
def ping():
    return {"status": "ok"}

# Embed & similarity endpoint for two sentences
@app.post("/api/similarity")
def similarity(pair: Pair):
    a = pair.a or ""
    b = pair.b or ""
    emb = model.encode([a, b], convert_to_numpy=True)
    score = float(cosine_similarity([emb[0]], [emb[1]])[0, 0])

    # label thresholds (tune later)
    if score >= 0.85:
        label = "High"
    elif score >= 0.65:
        label = "Medium"
    else:
        label = "Low"

    return {"score": score, "label": label}

# Endpoint: compare one document to a list of sentences (returns top matches)
@app.post("/api/compare")
def compare(payload: MultiDocs):
    doc = payload.doc_text or ""
    corpus = payload.corpus or []
    items = [doc] + corpus
    embeddings = model.encode(items, convert_to_numpy=True, show_progress_bar=False)
    doc_emb = embeddings[0]
    corpus_embs = embeddings[1:]
    sims = cosine_similarity([doc_emb], corpus_embs)[0].tolist()
    # return list of {"text":..., "score":...} sorted by score desc
    matches = [{"text": t, "score": float(s)} for t, s in zip(corpus, sims)]
    matches = sorted(matches, key=lambda x: x["score"], reverse=True)
    return {"matches": matches}
