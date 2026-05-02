import trafilatura
from playwright.sync_api import sync_playwright

def test_advanced_scraper(url):
    """
    Tests the hybrid scraper: 
    Playwright renders the JS -> Trafilatura cleans the text.
    """
    print(f"\n🚀 Starting advanced scrape for: {url}")
    
    try:
        with sync_playwright() as p:
            # 1. Start a headless browser instance
            # Use 'headless=False' if you want to see the browser window during testing
            browser = p.chromium.launch(headless=True)
            
            # 2. Open a new page and navigate to the URL
            page = browser.new_page()
            print("⏳ Rendering page (handling JavaScript)...")
            
            # Wait for the basic DOM to load
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Get the fully rendered HTML content
            rendered_html = page.content()
            browser.close()
            print("✅ HTML rendered successfully.")

        # 3. Extract the main text 'signal' using Trafilatura
        # This ignores headers, footers, and sidebars automatically.
        print("🧹 Cleaning content (removing boilerplate noise)...")
        extracted_text = trafilatura.extract(rendered_html)

        if extracted_text:
            print("\n--- 📄 Extracted Content Preview ---")
            # Show first 500 characters
            print(extracted_text[:500] + "...") 
            print("------------------------------------\n")
            print(f"📊 Total length: {len(extracted_text)} characters.")
        else:
            print("⚠️ Trafilatura could not find meaningful text on this page.")

    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")

if __name__ == "__main__":
    # Test with a known Sinhala Wikipedia page or any news site
    test_url = "https://si.wikipedia.org/wiki/ශ්‍රී_ලංකාව"
    test_advanced_scraper(test_url)