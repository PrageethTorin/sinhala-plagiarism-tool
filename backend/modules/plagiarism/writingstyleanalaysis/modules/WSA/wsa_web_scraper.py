import asyncio
import re
import urllib3
import requests

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
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def clean_text(text):
    """Normalizes Sinhala text for accurate similarity matching."""
    if not text:
        return ""
    text = re.sub(r"[^\u0D80-\u0DFF\s]", "", text)
    return " ".join(text.split()).strip()


async def get_internet_resources(query_text, num_results=7):
    """Discovery: fetch candidate URLs. Never raises."""
    if not query_text or not query_text.strip():
        return []

    links = []
    if DDGS_AVAILABLE and DDGS is not None:
        try:
            def fetch_search():
                with DDGS() as ddgs:
                    results = ddgs.text(query_text, max_results=12, region="lk")
                    return [r.get("href") or r.get("link") for r in results]

            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, fetch_search)

            for url in results:
                if not url:
                    continue
                if not url.lower().endswith(".pdf"):
                    links.append(url)
                if len(links) >= num_results:
                    break
        except Exception as e:
            print(f"[WSA] Search error: {e}")
    else:
        print("[WSA] DDGS not installed; web discovery disabled")

    if links:
        return links[:num_results]

    # Safe fallback
    first_token = query_text.strip().split(" ")[0]
    return [f"https://si.wikipedia.org/wiki/{first_token}"] if first_token else []


async def scrape_url_content(url, timeout=20):
    """Extract page text with Playwright or requests fallback. Never raises."""
    if not url:
        return ""

    try:
        if PLAYWRIGHT_AVAILABLE and async_playwright is not None:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(ignore_https_errors=True)
                    page = await context.new_page()
                    await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                    html_content = await page.content()
                    await browser.close()
                    return _extract_main_text(html_content)
            except Exception:
                # Hard fallback to requests path
                pass

        html_content = await _fetch_with_requests(url, timeout=timeout)
        return _extract_main_text(html_content)
    except Exception:
        return ""


async def _fetch_with_requests(url, timeout=20):
    def _sync_fetch():
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=False,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text

    return await asyncio.to_thread(_sync_fetch)


def _extract_main_text(html_content):
    if not html_content:
        return ""

    if TRAFILATURA_AVAILABLE and trafilatura is not None:
        try:
            text = trafilatura.extract(html_content, include_comments=False, no_fallback=False) or ""
            if text:
                return clean_text(text)
        except Exception:
            pass

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return clean_text(text)
    except Exception:
        return ""
