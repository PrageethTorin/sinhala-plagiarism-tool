# backend/semantic_similarity/websearch.py
import os
import requests
import time
from bs4 import BeautifulSoup
from .utils import normalize_sinhala, split_paragraphs

SEARCH_ENGINE_ID = os.getenv("CSE_ID", "57c81b2bf62594722")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def google_search(query: str, num: int = 3) -> list:
    if not GOOGLE_API_KEY:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": SEARCH_ENGINE_ID, "q": query, "num": num}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        return [it.get("link") for it in items if it.get("link")]
    except Exception:
        return []

def fetch_page_text(url: str, timeout: int = 8) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript","header","footer","svg"]):
            tag.extract()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]
        return "\n\n".join(paragraphs)
    except Exception:
        return ""

def fetch_web_texts_for_document(doc_text: str, queries_per_doc: int = 2, urls_per_query: int = 3, sleep_between: float = 0.8) -> list:
    if not doc_text:
        return []
    normalized = normalize_sinhala(doc_text)
    parts = split_paragraphs(normalized)
    queries = [normalized[:300]]
    if len(parts) > 1:
        queries.append(parts[len(parts)//2][:300])

    web_texts = []
    for q in queries[:queries_per_doc]:
        urls = google_search(q, num=urls_per_query)
        for u in urls:
            txt = fetch_page_text(u)
            if txt:
                web_texts.append(txt)
            time.sleep(sleep_between)
    return web_texts
