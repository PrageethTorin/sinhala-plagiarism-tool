import trafilatura
from ddgs import DDGS
from playwright.sync_api import sync_playwright
import urllib3

# Suppress SSL/InsecureRequest warnings common on .gov.lk websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_internet_resources(query_text, num_results=7):
    """
    DISCOVERY LAYER: Prioritizes Wikipedia results before searching other qualified URLs.
    """
    links = []
    print(f"📡 [Discovery] Prioritizing Wikipedia for: {query_text}")

    try:
        with DDGS() as ddgs:
            # --- PHASE 1: Wikipedia Targeted Search ---
            wiki_query = f"site:wikipedia.org {query_text}"
            wiki_results = ddgs.text(wiki_query, max_results=5, region='lk')
            
            for result in wiki_results:
                url = result['href']
                if "wikipedia.org" in url and not url.lower().endswith(".pdf"):
                    if url not in links:
                        links.append(url)
                        print(f"📚 [Wiki Priority Found] {url}")

            # --- PHASE 2: General Search (to fill remaining slots) ---
            if len(links) < num_results:
                print(f"📡 [Discovery] Filling remaining slots with general search...")
                general_results = ddgs.text(query_text, max_results=15, region='lk')
                
                for result in general_results:
                    url = result['href']
                    # Filter out PDFs and duplicates (don't add Wiki twice)
                    if not url.lower().endswith(".pdf") and url not in links:
                        links.append(url)
                        print(f"🔗 [Qualified Source] {url}")
                    
                    if len(links) >= num_results:
                        break

    except Exception as e:
        print(f"⚠️ Discovery Phase Error: {str(e)}")
        
    return links[:num_results] # Ensure we return exactly the requested amount

def scrape_url_content(url):
    """
    HYBRID SCRAPER: Combines JavaScript rendering with precision text extraction.
    """
    try:
        # 1. DYNAMIC RENDERING: Use Playwright to execute JavaScript
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # 30s timeout handles slow international or local servers
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            html_content = page.content()
            browser.close()

        # 2. SIGNAL EXTRACTION: Use Trafilatura to isolate main content
        extracted_text = trafilatura.extract(html_content, include_comments=False,
                                            include_tables=True, no_fallback=False)
        
        if extracted_text:
            # Clean text by removing newlines to support clean sentence-wise analysis
            return extracted_text.replace('\n', ' ').strip()
        return ""

    except Exception as e:
        print(f"❌ Scraper Error for {url}: {e}")
        return ""