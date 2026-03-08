import re
import asyncio
import trafilatura
from ddgs import DDGS
from playwright.async_api import async_playwright

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

_WS_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"[.!?।]+")


def _clean_query_text(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def _split_sentences(text: str):
    cleaned = _clean_query_text(text)
    if not cleaned:
        return []

    parts = _SENTENCE_SPLIT_RE.split(cleaned)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _pick_search_queries(text: str, max_queries: int = 3, max_len: int = 140):
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


def get_internet_resources(
    query_text: str,
    num_results: int = 3,
    region: str = "lk"
):
    links = []
    seen = set()

    try:
        queries = _pick_search_queries(query_text, max_queries=3, max_len=140)

        with DDGS() as ddgs:
            for query in queries:
                print(f"[WSA] Searching query chunk: {query}")
                results = ddgs.text(
                    query,
                    max_results=8,
                    region=region
                )

                for r in results:
                    url = r.get("href") or r.get("url")
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
                    links.append(url)

                    if len(links) >= num_results:
                        return links

    except Exception as e:
        print(f"[WSA] Discovery error: {e}")

    return links


async def scrape_url_content(url: str, timeout_ms: int = 30000) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            context = await browser.new_context(
                ignore_https_errors=True
            )

            page = await context.new_page()

            await page.goto(
                url,
                timeout=timeout_ms,
                wait_until="domcontentloaded"
            )

            await page.wait_for_timeout(1000)

            html = await page.content()

            await context.close()
            await browser.close()

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        if not extracted:
            return ""

        return _WS_RE.sub(" ", extracted).strip()[:20000]

    except Exception as e:
        print(f"[WSA] Scrape failed {url}: {e}")
        return ""


async def scrape_many(urls):
    tasks = [scrape_url_content(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []

    for url, text in zip(urls, results):
        if isinstance(text, Exception):
            text = ""

        output.append({
            "url": url,
            "text": text,
            "text_len": len(text)
        })

    return output