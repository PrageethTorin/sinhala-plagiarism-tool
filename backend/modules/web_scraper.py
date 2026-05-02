import trafilatura
from ddgs import DDGS
from playwright.sync_api import sync_playwright
import urllib3

# Suppress SSL/InsecureRequest warnings common on .gov.lk websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_internet_resources(query_text, num_results=6):
    """
    DISCOVERY LAYER: Identifies the top qualified URLs for the search tokens.
    Prioritizes Wikipedia URLs (first 4) then adds other sources (remaining 2).
    """
    wiki_links = []
    other_links = []
    print(f"📡 [Discovery] Searching for: {query_text}")
    try:
        with DDGS() as ddgs:
            # Fetch extra results to allow for filtering
            search_results = ddgs.text(query_text, max_results=20, region='lk')
        
        for result in search_results:
            url = result['href']
            # Only accept URLs that are not PDFs
            if not url.lower().endswith(".pdf"):
                # Prioritize Wikipedia URLs
                if "wikipedia.org" in url.lower():
                    wiki_links.append(url)
                    print(f"🔗 [Wikipedia Source] {url}")
                else:
                    other_links.append(url)
                    print(f"🔗 [Other Source] {url}")
        
        # Combine: first 4 Wikipedia URLs, then up to 2 other URLs
        links = wiki_links[:4] + other_links[:2]
        links = links[:num_results]  # Ensure we don't exceed num_results
        
    except Exception as e:
        print(f"⚠️ Discovery Phase Error: {str(e)}")
    return links

def scrape_url_content(url):
    """
    HYBRID SCRAPER: Combines JavaScript rendering with precision text extraction.
    Ensures 'reliable results' by removing boilerplate noise.
    """
    try:
        # 1. DYNAMIC RENDERING: Use Playwright to execute JavaScript
        with sync_playwright() as p:
            # Launch a headless browser (Chromium) to mimic a real user
            browser = p.chromium.launch(headless=True)
            # Create a context that bypasses SSL certificate verification errors
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # Navigate to the site and wait for the core DOM to load
            # A 30s timeout handles slow international or local servers
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Capture the fully rendered HTML (including JS-injected content)
            html_content = page.content()
            browser.close()

        # 2. SIGNAL EXTRACTION: Use Trafilatura to isolate main content
        # This removes headers, sidebars, and footers automatically
        extracted_text = trafilatura.extract(html_content, include_comments=False, 
                                            include_tables=True, no_fallback=False)
        
        if extracted_text:
            # Clean text by removing newlines to support clean sentence-wise analysis
            return extracted_text.replace('\n', ' ').strip()
        return ""

    except Exception as e:
        print(f"❌ Scraper Error for {url}: {e}")
        return ""