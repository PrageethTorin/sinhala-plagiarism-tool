# backend/semantic_similarity/sinhala_model.py
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "emb_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_model = None

def init_model(name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    global _model
    if _model is None:
        _model = SentenceTransformer(name)
    return _model

def _cache_key(text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.npy")

def load_embedding_cache(text: str):
    fp = _cache_key(text)
    if os.path.exists(fp):
        try:
            return np.load(fp)
        except Exception:
            return None
    return None

def save_embedding_cache(text: str, emb):
    fp = _cache_key(text)
    try:
        import numpy as _np
        _np.save(fp, emb)
    except Exception:
        pass

def batch_encode_with_cache(texts, model=None, batch_size: int = 64):
    if model is None:
        raise ValueError("model must be provided")
    embs = [None] * len(texts)
    to_encode = []
    to_encode_idx = []
    for i, t in enumerate(texts):
        cached = load_embedding_cache(t)
        if cached is not None:
            embs[i] = cached
        else:
            to_encode.append(t)
            to_encode_idx.append(i)
    if to_encode:
        encoded = model.encode(to_encode, convert_to_numpy=True, show_progress_bar=False)
        k = 0
        for idx in to_encode_idx:
            save_embedding_cache(to_encode[k], encoded[k])
            embs[idx] = encoded[k]
            k += 1
    import numpy as _np
    return _np.vstack(embs)
