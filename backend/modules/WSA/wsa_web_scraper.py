import re
import asyncio

# Try to import optional dependencies with graceful fallback
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("⚠️ Warning: trafilatura not installed - web content extraction disabled")

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    print("⚠️ Warning: duckduckgo-search not installed - web search disabled")

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️ Warning: playwright not installed - web scraping disabled")

def clean_text(text):
    """Normalizes Sinhala text for accurate similarity matching."""
    if not text: return ""
    # Keep only Sinhala Unicode range and spaces
    text = re.sub(r'[^\u0D80-\u0DFF\s]', '', text) 
    return " ".join(text.split()).strip()

async def get_internet_resources(query_text, num_results=7):
    """DISCOVERY: Fetches high-confidence URLs from the web."""
    links = []
    if not HAS_DDGS:
        print("⚠️ DuckDuckGo search disabled - trafilatura module not available")
        return links
    
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
    if not HAS_PLAYWRIGHT or not HAS_TRAFILATURA:
        print("⚠️ Web scraping disabled - playwright or trafilatura module not available")
        return ""
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            content = await page.content()
            await browser.close()
            text = trafilatura.extract(content, include_comments=False)
            return clean_text(text)
    except Exception as e:
        print(f"⚠️ Scraping error for {url}: {e}")
        return ""