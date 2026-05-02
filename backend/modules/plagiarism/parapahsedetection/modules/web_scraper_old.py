import re
import urllib3
import requests
from typing import List

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except Exception:
    trafilatura = None
    TRAFILATURA_AVAILABLE = False

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except Exception:
    DDGS = None
    DDGS_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    sync_playwright = None
    PLAYWRIGHT_AVAILABLE = False

# Suppress SSL/InsecureRequest warnings common on .gov.lk websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BAD_EXTENSIONS = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".zip", ".rar"
)

_BAD_DOMAINS = (
    "tiktok.com",
    "youtube.com",
    "youtu.be",
    "fandom.com",
    "wikiwand.com",
)

_SENTENCE_SPLIT_RE = re.compile(r"[.!?।]+")
_WS_RE = re.compile(r"\s+")


def _clean_query_text(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def _split_sentences(text: str) -> List[str]:
    cleaned = _clean_query_text(text)
    if not cleaned:
        return []

    parts = _SENTENCE_SPLIT_RE.split(cleaned)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _pick_search_queries(text: str, max_queries: int = 3, max_len: int = 140) -> List[str]:
    """
    For long text:
    - use first sentence
    - use longest / most distinctive sentences
    - keep only up to 3 short queries
    """
    cleaned = _clean_query_text(text)
    if not cleaned:
        return []

    if len(cleaned) <= max_len:
        return [cleaned]

    sentences = _split_sentences(cleaned)
    if not sentences:
        return [cleaned[:max_len]]

    ranked = sorted(
        sentences,
        key=lambda s: (len(set(s.split())), len(s)),
        reverse=True
    )

    queries = []

    first_sentence = sentences[0][:max_len]
    if first_sentence:
        queries.append(first_sentence)

    for sentence in ranked:
        q = sentence[:max_len]
        if q and q not in queries:
            queries.append(q)
        if len(queries) >= max_queries:
            break

    return queries[:max_queries]


def get_internet_resources(query_text, num_results=3) -> List[str]:
    """
    Discovery layer for candidate web URLs.

    Improvements:
    - long-query support using sentence-based search queries
    - fewer sources for speed
    - domain filtering for junk/slow sources
    """
    print(f"[Discovery] Searching for: {query_text}")

    all_links = []
    seen = set()

    queries = _pick_search_queries(query_text, max_queries=3, max_len=140)

    if DDGS_AVAILABLE and DDGS is not None:
        try:
            with DDGS() as ddgs:
                for query in queries:
                    print(f"[Discovery] Query chunk: {query}")
                    search_results = ddgs.text(query, max_results=8, region="lk")

                    for result in search_results:
                        url = result.get("href") or result.get("link") or result.get("url")
                        if not url:
                            continue

                        url_lower = url.lower()

                        if url_lower.endswith(_BAD_EXTENSIONS):
                            continue

                        if any(domain in url_lower for domain in _BAD_DOMAINS):
                            continue

                        if url in seen:
                            continue

                        seen.add(url)
                        all_links.append(url)

                        if len(all_links) >= num_results:
                            return all_links

        except Exception as e:
            print(f"[Discovery] DDGS search failed: {e}")
    else:
        print("[Discovery] DDGS is not installed, using fallback source list")

    if all_links:
        return all_links[:num_results]

    return _fallback_search(query_text, num_results)


def _fallback_search(query_text, num_results=3):
    """
    Minimal fallback source provider so the upstream pipeline does not fail.
    """
    sentences = _split_sentences(query_text)
    seed_source = sentences[0] if sentences else _clean_query_text(query_text)

    seed = seed_source.strip().split(" ")[0] if seed_source.strip() else ""
    wiki_url = f"https://si.wikipedia.org/wiki/{seed}" if seed else "https://si.wikipedia.org/"
    return [wiki_url][:num_results]


def scrape_url_content(url, timeout=12):
    """
    Scrape URL content using Playwright or requests + trafilatura.
    Falls back to BeautifulSoup extraction if needed.
    """
    try:
        html_content = ""

        if PLAYWRIGHT_AVAILABLE and sync_playwright is not None:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(ignore_https_errors=True)
                    page = context.new_page()
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(1000)
                    html_content = page.content()
                    browser.close()
            except Exception as e:
                print(f"[Scraper] Playwright path failed for {url}: {e}")

        if not html_content:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=False,
                allow_redirects=True,
            )
            response.raise_for_status()
            html_content = response.text

        extracted_text = ""
        if TRAFILATURA_AVAILABLE and trafilatura is not None:
            try:
                extracted_text = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                    favor_precision=False,
                ) or ""
            except Exception:
                extracted_text = ""

        if extracted_text and len(extracted_text.strip()) > 100:
            return " ".join(extracted_text.split())[:20000]

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            cleaned = " ".join(text.split())

            if len(cleaned) > 100:
                return cleaned[:20000]

        except Exception as e:
            print(f"[Scraper] BeautifulSoup fallback failed for {url}: {e}")

        return ""

    except requests.exceptions.Timeout:
        print(f"[Scraper] Timeout fetching {url}")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"[Scraper] Request error for {url}: {e}")
        return ""
    except Exception as e:
        print(f"[Scraper] Unexpected error for {url}: {e}")
        return ""