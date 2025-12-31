# backend/modules/semantic_similarity/utils.py
import re
from typing import List, Optional
import os
import pickle
import hashlib

# -------------------------
# Text helpers (Sinhala)
# -------------------------
def normalize_sinhala(text: Optional[str]) -> str:
    if not text:
        return ""
    t = str(text).lower()
    t = t.replace("\u200d", "").replace("\u200c", "")
    # keep Sinhala unicode range + spaces
    t = re.sub(r"[^\u0D80-\u0DFF\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def split_paragraphs(text: Optional[str]) -> List[str]:
    """Split text into paragraphs (two or more newlines) or fallback to whole text."""
    if not text:
        return []
    parts = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', str(text)) if p.strip()]
    if not parts and str(text).strip():
        parts = [str(text).strip()]
    return parts

def split_sentences_simple(text: Optional[str]) -> List[str]:
    """
    Naive sentence splitter: looks for ., ?, !, or danda (U+0964) then whitespace/newline.
    This is simple but useful for paragraph-level stylometrics.
    """
    if not text:
        return []
    # include danda \u0964 (used in many Indic scripts) as sentence end
    parts = re.split(r'(?<=[\.\?\!\u0964])\s+|\n+', str(text))
    parts = [p.strip() for p in parts if p.strip()]
    return parts

# -------------------------
# Embedding cache utilities
# -------------------------
# Cache directory is located next to this utils.py (module folder)
CACHE_DIR = os.path.join(os.path.dirname(__file__), "embedding_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _hash_text(text: str) -> str:
    """Return an md5 hex digest for a text (used as filename)."""
    if text is None:
        text = ""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return h

def save_embedding_cache(text: str, embedding) -> None:
    """
    Save embedding (numpy array or list) to local cache file.
    Silently ignores failures (cache is optional).
    """
    try:
        fname = os.path.join(CACHE_DIR, _hash_text(text) + ".pkl")
        with open(fname, "wb") as f:
            pickle.dump(embedding, f)
    except Exception:
        # don't crash on cache errors
        return

def load_embedding_cache(text: str):
    """
    Load embedding from cache if present. Returns None if not found or on error.
    """
    try:
        fname = os.path.join(CACHE_DIR, _hash_text(text) + ".pkl")
        if not os.path.exists(fname):
            return None
        with open(fname, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None
