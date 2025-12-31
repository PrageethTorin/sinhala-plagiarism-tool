from typing import List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .utils import normalize_sinhala, split_paragraphs, split_sentences_simple
from .sinhala_model import init_model, batch_encode_with_cache
from .lexical import lexical_similarity
from .stylometric import stylometric_similarity
from .websearch import fetch_web_texts_for_document
from .googledoc import fetch_google_doc_text_service
import os

# ===============================
# WEIGHTS (Sinhala-balanced)
# ===============================
W_SEM = 0.60
W_LEX = 0.30
W_STYL = 0.10

# ===============================
# MULTILINGUAL PARAPHRASE MODEL
# ===============================
MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    os.path.join(
        os.path.dirname(__file__),
        "training",
        "fine_tuned_sinhala_model"
    )
)


model = init_model(MODEL_NAME)


def combined_score(semantic: float, lexical: float, stylometric: float) -> float:
    return (W_SEM * semantic) + (W_LEX * lexical) + (W_STYL * stylometric)


# --------------------------------------------------
# Paragraph ↔ Paragraph (debug / testing)
# --------------------------------------------------
def process_paragraph_similarity(p1: str, p2: str):
    pa = normalize_sinhala(p1)
    pb = normalize_sinhala(p2)

    embs = batch_encode_with_cache([pa, pb], model=model)
    sem = float(cosine_similarity([embs[0]], [embs[1]])[0, 0])
    lex = lexical_similarity(pa, pb)
    styl = stylometric_similarity(pa, pb)

    comb = combined_score(sem, lex, styl)

    return {
        "semantic": round(sem, 4),
        "lexical": round(lex, 4),
        "stylometric": round(styl, 4),
        "combined": round(comb, 4),
        "percentage": round(comb * 100, 2),
    }


# --------------------------------------------------
# Document ↔ Corpus (paragraph level)
# --------------------------------------------------
def process_document_text(
    doc_text: str,
    corpus: Optional[List[str]] = None,
    top_k: int = 3
):
    doc = normalize_sinhala(doc_text)
    paras = split_paragraphs(doc)

    # IMPORTANT: split corpus into paragraphs too
    corpus_paras = []
    for c in (corpus or []):
        corpus_paras.extend(split_paragraphs(normalize_sinhala(c)))

    if not paras or not corpus_paras:
        return {"paragraphs": [], "document_score": 0.0}

    items = paras + corpus_paras
    embs = batch_encode_with_cache(items, model=model)

    paras_emb = embs[:len(paras)]
    corpus_emb = embs[len(paras):]

    paragraphs_out = []

    for i, p in enumerate(paras):
        sems = cosine_similarity([paras_emb[i]], corpus_emb)[0]

        matches = []
        for j, c in enumerate(corpus_paras):
            sem = float(sems[j])
            lex = lexical_similarity(p, c)
            styl = stylometric_similarity(p, c)
            comb = combined_score(sem, lex, styl)

            matches.append({
                "corpus_index": j,
                "corpus_text": c,
                "semantic": round(sem, 4),
                "lexical": round(lex, 4),
                "stylometric": round(styl, 4),
                "combined": round(comb, 4),
            })

        matches_sorted = sorted(matches, key=lambda x: x["combined"], reverse=True)[:top_k]
        paragraph_score = matches_sorted[0]["combined"] if matches_sorted else 0.0

        paragraphs_out.append({
            "index": i,
            "text": p,
            "matches": matches_sorted,
            "paragraph_score": round(paragraph_score * 100, 2),
        })

    overall = round(np.mean([p["paragraph_score"] for p in paragraphs_out]), 2)

    return {
        "paragraphs": paragraphs_out,
        "document_score": overall,
    }


# --------------------------------------------------
# Paragraph → Web / Google Doc (MAIN FEATURE)
# --------------------------------------------------
def process_paragraph_web_check(
    paragraph: str,
    top_k: int = 3,
    google_doc_url: Optional[str] = None,
    use_web_search: bool = True
):
    p = normalize_sinhala(paragraph)
    if not p:
        return {"matches": [], "paragraph_score": 0.0}

    corpus_texts = []

    if use_web_search:
        web_docs = fetch_web_texts_for_document(p)
        for w in web_docs:
            corpus_texts.extend(split_paragraphs(w))

    if google_doc_url:
        try:
            doc_id = google_doc_url.split("/d/")[1].split("/")[0]
            gtext = fetch_google_doc_text_service(doc_id)
            if gtext:
                corpus_texts.extend(split_paragraphs(gtext))
        except Exception:
            pass

    if not corpus_texts:
        return {"matches": [], "paragraph_score": 0.0}

    res = process_document_text(p, corpus_texts, top_k)
    para = res["paragraphs"][0]

    return {
        "matches": para["matches"],
        "paragraph_score": para["paragraph_score"],
    }


# --------------------------------------------------
# Document ↔ Document (sentence level)
# --------------------------------------------------
def process_doc_compare(doc_a: str, doc_b: str, top_k: int = 3):
    a = normalize_sinhala(doc_a)
    b = normalize_sinhala(doc_b)

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

            result_pairs.append({
                "a_index": i,
                "a_text": sents_a[i],
                "b_index": j,
                "b_text": sents_b[j],
                "semantic": round(sem, 4),
                "lexical": round(lex, 4),
                "stylometric": round(styl, 4),
                "combined": round(comb, 4),
            })

    best_per_a = []
    for i in range(len(sents_a)):
        row = [r for r in result_pairs if r["a_index"] == i]
        if row:
            best_per_a.append(max(r["combined"] for r in row))

    doc_score = float(np.mean(best_per_a)) if best_per_a else 0.0

    return {
        "pairs": result_pairs,
        "document_score": round(doc_score * 100, 2),
    }
