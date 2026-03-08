#bridge between web text and your hybrid detector#
from .web_provider import fetch_web_paragraphs
from ..approved_hybrid import ApprovedHybridDetector

def web_assisted_similarity(user_text: str, top_k: int = 5):
    detector = ApprovedHybridDetector()
    web_texts = fetch_web_paragraphs(user_text)

    results = []

    for text in web_texts:
        result = detector.detect(user_text, text)
        result["matched_text"] = text
        results.append(result)

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]
