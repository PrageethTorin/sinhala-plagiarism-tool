import urllib3
import requests
import time
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

_SCRAPE_CACHE = {}
_SCRAPE_CACHE_TTL_S = 600
_BLOCKED_DOMAINS = ("youtube.com", "youtu.be", "tiktok.com", "facebook.com")
_LOW_QUALITY_DOMAINS = (
    "groups.google.com",
    "huggingface.co/datasets",
    "d1.islamhouse.com",
)
_HARD_BLOCK_DOMAINS = (
    "pinterest.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "x.com",
)


def _domain_priority(url: str) -> int:
    u = (url or "").lower()
    if "si.wikipedia.org" in u:
        return 0
    if ".gov.lk" in u:
        return 1
    if ".ac.lk" in u or ".edu" in u:
        return 2
    if any(d in u for d in _LOW_QUALITY_DOMAINS):
        return 9
    return 5


def get_internet_resources(query_text, num_results=7) -> List[str]:
    """
    Discovery layer for candidate web URLs.
    Falls back to static sources if DDGS is unavailable or fails.
    """
    links = []
    low_quality_links = []
    seen = set()
    print(f"[Discovery] Searching for: {query_text}")

    if DDGS_AVAILABLE and DDGS is not None:
        try:
            with DDGS() as ddgs:
                queries = [
                    f"\"{query_text}\"",
                    f"site:si.wikipedia.org \"{query_text}\"",
                    query_text,
                ]
                for q in queries:
                    search_results = ddgs.text(q, max_results=20, region="lk")

                    for result in search_results:
                        url = result.get("href") or result.get("link")
                        if not url:
                            continue
                        ul = url.lower()
                        if ul.endswith(".pdf"):
                            continue
                        if any(domain in ul for domain in _BLOCKED_DOMAINS):
                            continue
                        if any(domain in ul for domain in _HARD_BLOCK_DOMAINS):
                            continue
                        if url in seen:
                            continue
                        seen.add(url)

                        if any(domain in ul for domain in _LOW_QUALITY_DOMAINS):
                            low_quality_links.append(url)
                        else:
                            links.append(url)

                    if len(links) >= num_results:
                        break
        except Exception as e:
            print(f"[Discovery] DDGS search failed: {e}")
    else:
        print("[Discovery] DDGS is not installed, using fallback source list")

    if links:
        links.sort(key=_domain_priority)
        if len(links) < num_results and low_quality_links:
            links.extend(low_quality_links)
        return links[:num_results]
    return _fallback_search(query_text, num_results)


def _fallback_search(query_text, num_results=5):
    """
    Minimal fallback source provider so the upstream pipeline does not fail.
    """
    seed = query_text.strip().split(" ")[0] if query_text.strip() else ""
    wiki_url = f"https://si.wikipedia.org/wiki/{seed}" if seed else "https://si.wikipedia.org/"
    return [wiki_url][:num_results]


def scrape_url_content(url, timeout=15):
    """
    Scrape URL content using requests + trafilatura.
    Falls back to BeautifulSoup extraction if trafilatura is unavailable/weak.
    """
    try:
        now = time.time()
        cached = _SCRAPE_CACHE.get(url)
        if cached and (now - cached["ts"]) < _SCRAPE_CACHE_TTL_S:
            return cached["text"]

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
            normalized = " ".join(extracted_text.split())
            _SCRAPE_CACHE[url] = {"ts": now, "text": normalized}
            return normalized

        # Fallback to Playwright only if the static extraction was weak.
        if PLAYWRIGHT_AVAILABLE and sync_playwright is not None:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(ignore_https_errors=True)
                    page = context.new_page()
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    html_content = page.content()
                    browser.close()
            except Exception as e:
                print(f"[Scraper] Playwright path failed for {url}: {e}")

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            cleaned = " ".join(text.split())
            if len(cleaned) > 100:
                trimmed = cleaned[:20000]
                _SCRAPE_CACHE[url] = {"ts": now, "text": trimmed}
                return trimmed
        except Exception as e:
            print(f"[Scraper] BeautifulSoup fallback failed for {url}: {e}")

        return ""

    except requests.exceptions.Timeout:
        print(f"[Scraper] Timeout fetching {url}")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"[Scraper] Request error for {url}: {e}")       
    except Exception as e:
        print(f"[Scraper] Unexpected error for {url}: {e}")
        return ""
