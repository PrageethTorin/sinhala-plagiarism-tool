import os
import requests
import time
from bs4 import BeautifulSoup
from .utils import normalize_sinhala, split_paragraphs

SEARCH_ENGINE_ID = os.getenv("CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def google_search(query: str, num: int = 3) -> list:
    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": num
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return [item["link"] for item in r.json().get("items", [])]
    except Exception:
        return []


def fetch_page_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "header", "footer", "noscript"]):
            tag.extract()

        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 60]

        return "\n\n".join(paragraphs)
    except Exception:
        return ""


def fetch_web_texts_for_document(doc_text: str) -> list:
    normalized = normalize_sinhala(doc_text)
    paras = split_paragraphs(normalized)

    # 🔑 KEY FIX: SHORT QUERY FOR BETTER GOOGLE MATCH
    query = paras[0][:120] if paras else normalized[:120]

    urls = google_search(query, num=3)
    web_paragraphs = []

    for url in urls:
        text = fetch_page_text(url)
        if text:
            for p in split_paragraphs(text):
                if len(p) > 60:
                    web_paragraphs.append(normalize_sinhala(p))
        time.sleep(0.8)

    return web_paragraphs
