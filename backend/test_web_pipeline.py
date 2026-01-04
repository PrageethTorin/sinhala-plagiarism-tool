import sys
import os
import time

# Ensure Python can find the 'modules' folder where web_scraper.py lives
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from web_scraper import get_internet_resources, scrape_url_content

def test_web_discovery():
    # NEW TEST QUERY: "Natural Language Processing techniques for Sinhala language in Sri Lanka"
    # This matches the core research topic of your MSc source document 
    test_query = "ශ්‍රී ලංකාවේ සිංහල භාෂාව සඳහා ස්වභාවික භාෂා සැකසුම් තාක්ෂණය" 
    
    print(f"🚀 [TEST 1] Testing Search Discovery for: '{test_query}'")
    print("📡 Requesting top 5 non-PDF URLs from DuckDuckGo...")
    
    # We use num_results=5 to keep the test fast and avoid IP blocks [cite: 770]
    links = get_internet_resources(test_query, num_results=5)
    
    if links:
        print(f"✅ Found {len(links)} candidate URLs:")
        for i, link in enumerate(links):
            print(f"   {i+1}. {link}")
        return links[0] 
    else:
        print("❌ No links found.")
        print("💡 Tip: Wait 10 minutes or check if Google is rate-limiting your IP.")
        return None

def test_html_extraction(url):
    print(f"\n🚀 [TEST 2] Testing 'HTML Passer' logic for: {url}")
    print("⏳ Connecting and extracting <p> tag content...")
    
    # Implementing the Jsoup-style extraction logic from the research [cite: 829, 830]
    content = scrape_url_content(url)
    
    if content:
        print("✅ Web Content Extracted Successfully!")
        print("-" * 50)
        # Verify the first 250 characters of the scraped body text [cite: 858, 864]
        print(f"📝 Preview: {content[:250]}...")
        print("-" * 50)
        
        # Calculate word count to verify data density [cite: 387, 402]
        word_count = len(content.split())
        print(f"📊 Total tokens extracted: {word_count}")
    else:
        print("❌ Extraction failed. The website security might be blocking the scraper[cite: 1116].")

if __name__ == "__main__":
    start_time = time.time()
    
    # Following the Waterfall methodology: Discovery first, then Extraction [cite: 314, 343]
    first_url = test_web_discovery()
    
    if first_url:
        test_html_extraction(first_url)
    
    end_time = time.time()
    print(f"\n⏱️ Total Test Time: {round(end_time - start_time, 2)} seconds.")