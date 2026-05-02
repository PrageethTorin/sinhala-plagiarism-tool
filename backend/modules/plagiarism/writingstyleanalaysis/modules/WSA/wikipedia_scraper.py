import requests
import pandas as pd
import re
import time
import os

# Absolute path targeting the file in your specific folder
current_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(current_dir, 'training_data.csv')

def scrape_sinhala_wikipedia(target_rows=1000):
    api_url = "https://si.wikipedia.org/w/api.php"
    collected_sentences = []
    
    # Identify the script to Wikipedia to avoid 403/connection errors
    headers = {
        'User-Agent': 'SinhalaPlagiarismTool/1.0 (Research Project; contact: your_email@example.com)'
    }

    print(f"🚀 Target File: {CSV_FILE}")
    print(f"🚀 Starting API Scraper to collect {target_rows} rows...")

    while len(collected_sentences) < target_rows:
        try:
            # 1. Fetch random article titles
            params = {
                "action": "query",
                "format": "json",
                "list": "random",
                "rnnamespace": 0,
                "rnlimit": 10 
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            
            # Check if response is valid JSON
            if response.status_code != 200:
                print(f"⚠️ Server error {response.status_code}. Retrying...")
                time.sleep(5)
                continue
                
            data = response.json()
            titles = [page['title'] for page in data['query']['random']]

            for title in titles:
                # 2. Get plain text content
                content_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "extracts",
                    "explaintext": True,
                }
                
                content_resp = requests.get(api_url, params=content_params, headers=headers, timeout=15).json()
                pages = content_resp['query']['pages']
                page_id = list(pages.keys())[0]
                
                if page_id == "-1": continue # Skip if page not found
                
                full_text = pages[page_id].get('extract', '')

                # 3. Clean and split into sentences
                text = re.sub(r'\(.*?\)|\[.*?\]', '', full_text)
                sentences = re.split(r'[.|।|?|!]', text)
                
                for s in sentences:
                    clean_s = s.strip()
                    # Filter for research quality: 8 to 30 words
                    if 8 <= len(clean_s.split()) <= 30:
                        collected_sentences.append(clean_s)

                print(f"✅ Total Collected: {len(collected_sentences)} / {target_rows} (Added from: {title})")
                
                if len(collected_sentences) >= target_rows:
                    break

            time.sleep(1) # Safety delay

        except Exception as e:
            print(f"⚠️ Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            continue

    # 4. Save to CSV
    df = pd.DataFrame(collected_sentences[:target_rows], columns=['text'])
    df.to_csv(CSV_FILE, mode='a', index=False, header=not os.path.exists(CSV_FILE))
    
    print(f"\n🎉 SUCCESS! {len(df)} rows added to {CSV_FILE}")

if __name__ == "__main__":
    scrape_sinhala_wikipedia(target_rows=1000)