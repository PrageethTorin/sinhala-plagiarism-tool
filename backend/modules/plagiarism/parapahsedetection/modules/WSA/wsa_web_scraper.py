import trafilatura
import re
import asyncio
from ddgs import DDGS 
from playwright.async_api import async_playwright

def clean_text(text):
    """Normalizes Sinhala text for accurate similarity matching."""
    if not text: return ""
    # Keep only Sinhala Unicode range and spaces
    text = re.sub(r'[^\u0D80-\u0DFF\s]', '', text) 
    return " ".join(text.split()).strip()

async def get_internet_resources(query_text, num_results=7):
    """DISCOVERY: Fetches high-confidence URLs from the web."""
    links = []
    try:
        def fetch_search():
            with DDGS() as ddgs:
                return [r['href'] for r in ddgs.text(query_text, max_results=12, region='lk')]
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, fetch_search)
        
        for url in results:
            if not url.lower().endswith(".pdf"):
                links.append(url)
            if len(links) >= num_results: break
    except Exception as e:
        print(f"📡 Search Error: {e}")
    return links

async def scrape_url_content(url):
    """EXTRACTION: Scrapes core content and cleans it."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            content = await page.content()
            await browser.close()
            text = trafilatura.extract(content, include_comments=False)
            return clean_text(text)
    except Exception:
        return ""