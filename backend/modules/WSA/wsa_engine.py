import os
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from wsa_web_scraper import get_internet_resources, scrape_url_content, clean_text

class WSAAnalyzer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.vectorizer = joblib.load(os.path.join(current_dir, 'vectorizer.pkl'))

    def calculate_ttr(self, text):
        words = text.split()
        if not words: return 0
        return (len(set(words)) / len(words)) * 100

    async def check_text(self, input_text):
        sentences = [s.strip() for s in input_text.split('.') if len(s.strip()) > 5]
        if len(sentences) < 1:
            return {"ratio_data": {"style_change_ratio": 0, "matched_url": "No source found", "sentence_map": []}}

        # Establish Baseline from first 2 sentences
        base_len = np.mean([len(s.split()) for s in sentences[:2]])
        base_ttr = np.mean([self.calculate_ttr(s) for s in sentences[:2]])

        sentence_map = []
        flagged_count = 0

        for i, s in enumerate(sentences):
            curr_len = len(s.split())
            curr_ttr = self.calculate_ttr(s)
            
            if i < 2:
                is_outlier = False
            else:
                # FIXED: Cast NumPy result to standard Python bool to prevent FastAPI crash
                is_outlier = bool(abs(curr_len - base_len) > (base_len * 0.20) or \
                                  abs(curr_ttr - base_ttr) > (base_ttr * 0.20))
            
            if is_outlier: flagged_count += 1
            
            sentence_map.append({
                "id": i + 1, 
                "length": int(curr_len), # Ensure integer
                "lexical_ttr": float(round(curr_ttr, 2)), # Ensure float
                "is_outlier": is_outlier
            })

        # Internet Discovery Layer
        clean_input = clean_text(input_text)
        links = await get_internet_resources(clean_input[:150], num_results=7)
        
        best_url, max_sim = "No source found", 0
        input_vec = self.vectorizer.transform([clean_input])

        for url in links:
            web_text = await scrape_url_content(url)
            if web_text:
                web_vec = self.vectorizer.transform([web_text])
                sim = float(cosine_similarity(input_vec, web_vec)[0][0])
                if sim > max_sim:
                    max_sim, best_url = sim, url

        final_url = best_url if max_sim > 0.18 else "No source found"
        style_ratio = round((flagged_count / len(sentences)) * 100, 2)

        return {
            "ratio_data": {
                "style_change_ratio": float(style_ratio),
                "matched_url": final_url,
                "similarity_score": float(round(max_sim * 100, 2)),
                "sentence_map": sentence_map
            }
        }