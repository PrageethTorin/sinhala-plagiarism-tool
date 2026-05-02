from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

semantic_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
char_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))


def semantic_similarity(a, b):
    e1 = semantic_model.encode(a, convert_to_tensor=True)
    e2 = semantic_model.encode(b, convert_to_tensor=True)
    return util.cos_sim(e1, e2).item() * 100


def paraphrase_similarity(a, b):
    tfidf = char_vectorizer.fit_transform([a, b])
    return cosine_similarity(tfidf[0], tfidf[1])[0][0] * 100


def style_similarity(a, b):
    return (min(len(a), len(b)) / max(len(a), len(b))) * 100
