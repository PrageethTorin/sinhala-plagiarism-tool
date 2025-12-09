# backend/semantic_similarity/engine.py
from typing import List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .utils import normalize_sinhala, split_paragraphs, split_sentences_simple, load_embedding_cache, save_embedding_cache
from .sinhala_model import init_model, batch_encode_with_cache
from .lexical import lexical_similarity
from .stylometric import stylometric_similarity
from .websearch import fetch_web_texts_for_document
from .googledoc import fetch_google_doc_text_service
import os

# weights
W_SEM = 0.65
W_LEX = 0.25
W_STYL = 0.10

# initialize model (init_model loads a SentenceTransformer)
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
model = init_model(MODEL_NAME)

def combined_score(semantic: float, lexical: float, stylometric: float,
                   w_sem=W_SEM, w_lex=W_LEX, w_styl=W_STYL) -> float:
    return w_sem * semantic + w_lex * lexical + w_styl * stylometric

# process two paragraphs
def process_paragraph_similarity(p1: str, p2: str):
    pa = normalize_sinhala(p1 or "")
    pb = normalize_sinhala(p2 or "")
    embs = batch_encode_with_cache([pa, pb], model=model)
    sem = float(cosine_similarity([embs[0]], [embs[1]])[0,0]) if embs.shape[0] >= 2 else 0.0
    lex = lexical_similarity(pa, pb)
    styl = stylometric_similarity(pa, pb)
    comb = combined_score(sem, lex, styl)
    return {"semantic": sem, "lexical": lex, "stylometric": styl, "combined": comb, "percentage": round(comb*100,2)}

# core: compare document text (split into paragraphs) vs corpus list[str]
def process_document_text(doc_text: str, corpus: Optional[List[str]] = None, top_k: int = 3):
    doc = normalize_sinhala(doc_text or "")
    paras = split_paragraphs(doc)
    corpus = [normalize_sinhala(c) for c in (corpus or [])]
    top_k = max(1, int(top_k or 3))

    if not paras:
        return {"paragraphs": [], "document_score": 0.0}

    if not corpus:
        paragraphs_out = [{"index": i, "text": p, "matches": [], "paragraph_score": 0.0} for i,p in enumerate(paras)]
        return {"paragraphs": paragraphs_out, "document_score": 0.0}

    items = paras + corpus
    embs = batch_encode_with_cache(items, model=model)
    paras_emb = embs[:len(paras)]
    corpus_emb = embs[len(paras):]

    # TF-IDF vectors handled in lexical_similarity
    paragraphs_out = []
    for i, p in enumerate(paras):
        sems = cosine_similarity([paras_emb[i]], corpus_emb)[0].tolist() if corpus_emb.size else [0.0]*len(corpus)
        matches = []
        for j, c in enumerate(corpus):
            sem = float(sems[j]) if j < len(sems) else 0.0
            lex = lexical_similarity(p, c)
            styl = stylometric_similarity(p, c)
            comb = combined_score(sem, lex, styl)
            matches.append({"corpus_index": j, "corpus_text": c, "semantic": sem, "lexical": lex, "stylometric": styl, "combined": comb})
        matches_sorted = sorted(matches, key=lambda x: x["combined"], reverse=True)[:top_k]
        paragraph_score = matches_sorted[0]["combined"] if matches_sorted else 0.0
        paragraphs_out.append({"index": i, "text": p, "matches": matches_sorted, "paragraph_score": round(paragraph_score*100,2)})

    overall = round(float(np.mean([p["paragraph_score"] for p in paragraphs_out])) if paragraphs_out else 0.0, 2)
    return {"paragraphs": paragraphs_out, "document_score": overall}

# doc_compare: sentence-to-sentence between two docs
def process_doc_compare(doc_a: str, doc_b: str, top_k: int = 3):
    a = normalize_sinhala(doc_a or "")
    b = normalize_sinhala(doc_b or "")
    sents_a = split_sentences_simple(a)
    sents_b = split_sentences_simple(b)
    if not sents_a or not sents_b:
        return {"pairs": [], "document_score": 0.0}
    items = sents_a + sents_b
    embs = batch_encode_with_cache(items, model=model)
    embs_a = embs[:len(sents_a)]
    embs_b = embs[len(sents_a):]
    sims = cosine_similarity(embs_a, embs_b)
    result_pairs = []
    for i, row in enumerate(sims):
        idxs = row.argsort()[::-1][:top_k]
        for j in idxs:
            sem = float(row[j])
            lex = lexical_similarity(sents_a[i], sents_b[j])
            styl = stylometric_similarity(sents_a[i], sents_b[j])
            comb = combined_score(sem, lex, styl)
            result_pairs.append({"a_index": i, "a_text": sents_a[i], "b_index": j, "b_text": sents_b[j], "semantic": sem, "lexical": lex, "stylometric": styl, "combined": comb})
    result_pairs = sorted(result_pairs, key=lambda x: x["combined"], reverse=True)
    best_per_a = []
    for i in range(len(sents_a)):
        row = [r for r in result_pairs if r["a_index"] == i]
        if row:
            best_per_a.append(max(r["combined"] for r in row))
    doc_score = float(np.mean(best_per_a)) if best_per_a else 0.0
    return {"pairs": result_pairs, "document_score": round(doc_score*100,2)}

# Paragraph web check: given one paragraph, build corpus via web/doc and compare
def process_paragraph_web_check(paragraph: str, top_k: int = 3, google_doc_url: Optional[str] = None, use_web_search: bool = True):
    p = normalize_sinhala((paragraph or "").strip())
    top_k = max(1, int(top_k or 3))
    if not p:
        return {"error": "Empty paragraph", "matches": [], "paragraph_score": 0.0}
    corpus_texts = []
    if use_web_search:
        web_texts = fetch_web_texts_for_document(p)
        if web_texts:
            corpus_texts.extend(web_texts)
    if google_doc_url:
        doc_id = None
        try:
            if "/d/" in google_doc_url:
                doc_id = google_doc_url.split("/d/")[1].split("/")[0]
            else:
                doc_id = google_doc_url.strip()
        except Exception:
            doc_id = None
        if doc_id:
            gtext = fetch_google_doc_text_service(doc_id)
            if gtext:
                corpus_texts.append(gtext)
    if not corpus_texts:
        return {"matches": [], "paragraph_score": 0.0, "note": "No web or doc sources found"}
    res = process_document_text(doc_text=p, corpus=corpus_texts, top_k=top_k)
    paragraph_out = res["paragraphs"][0] if res.get("paragraphs") else {"index":0,"text":p,"matches":[], "paragraph_score":0.0}
    return {"matches": paragraph_out["matches"], "paragraph_score": paragraph_out["paragraph_score"], "document_score": res.get("document_score", 0.0)}
