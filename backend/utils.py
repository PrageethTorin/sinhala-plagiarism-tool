# backend/utils.py
import unicodedata, re, os, hashlib, numpy as np
from typing import List

def normalize_sinhala(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[“”«»]", '"', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def split_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return parts if parts else ([text.strip()] if text.strip() else [])

def split_sentences_simple(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r'(?<=[\.\?!\n])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

# simple disk embedding cache
def _cache_path_for_text(text, cache_dir="backend/cache"):
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.sha1(text.encode('utf-8')).hexdigest()
    return os.path.join(cache_dir, f"{key}.npy")

def save_embedding_cache(text, emb, cache_dir="backend/cache"):
    path = _cache_path_for_text(text, cache_dir)
    np.save(path, emb)

def load_embedding_cache(text, cache_dir="backend/cache"):
    path = _cache_path_for_text(text, cache_dir)
    if os.path.exists(path):
        return np.load(path)
    return None
