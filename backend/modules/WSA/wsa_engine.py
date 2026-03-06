import os
import joblib
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from wsa_web_scraper import get_internet_resources, scrape_url_content, clean_text
from extractor import StyleExtractor
from db_bridge import DBBridge

class WSAAnalyzer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.vectorizer = joblib.load(os.path.join(current_dir, 'vectorizer.pkl'))
        self.extractor = StyleExtractor()
        self.db = DBBridge()

    def calculate_ttr(self, text):
        words = text.split()
        if not words: return 0
        return (len(set(words)) / len(words)) * 100

    async def check_text(self, input_text):
        try:
            # 1. Local Database Collusion Check (PRE-SAVE)
            previous_submissions = self.db.get_all_previous_submissions()
            highest_local_score = 0.0
            input_clean = clean_text(input_text)
            input_vec = self.vectorizer.transform([input_clean])
            input_vec_1d = input_vec.toarray().flatten() if hasattr(input_vec, 'toarray') else input_vec.flatten()

            for _, prev_vec_blob in previous_submissions:
                try:
                    prev_vec = pickle.loads(prev_vec_blob)
                    prev_vec_1d = prev_vec.toarray().flatten() if hasattr(prev_vec, 'toarray') else prev_vec.flatten()
                    
                    # Check dimension compatibility before comparing
                    if len(input_vec_1d) != len(prev_vec_1d):
                        print(f"⚠️ Skipping vector with incompatible dimensions: input={len(input_vec_1d)}, stored={len(prev_vec_1d)}")
                        continue
                    
                    # Reshape for 2D comparison
                    sim = float(cosine_similarity(input_vec.reshape(1,-1), prev_vec.reshape(1,-1))[0][0])
                    if sim > highest_local_score:
                        highest_local_score = sim
                except Exception as e:
                    print(f"⚠️ Error comparing vectors: {e}")
                    continue

            # 2. Stylistic Analysis
            sentences = [s.strip() for s in input_text.split('.') if len(s.strip()) > 5]
            if not sentences:
                return {"ratio_data": {"style_change_ratio": 0, "matched_url": "No source found", "sentence_map": []}}

            base_len = np.mean([len(s.split()) for s in sentences[:2]])
            base_ttr = np.mean([self.calculate_ttr(s) for s in sentences[:2]])
            
            sentence_map = []
            flagged_words = 0
            all_words = input_text.split()
            avg_word_len = np.mean([len(w) for w in all_words]) if all_words else 5.0

            for i, s in enumerate(sentences):
                words_in_sent = s.split()
                word_objects = []
                sent_has_shift = False

                for w in words_in_sent:
                    # Detect morphological shift
                    is_shift = self.extractor.is_word_a_style_shift(w, avg_word_len)
                    if is_shift:
                        flagged_words += 1
                        sent_has_shift = True
                    word_objects.append({"text": w, "is_style_shift": is_shift})

                # Sentence level baseline outlier check
                is_outlier = False if i < 2 else bool(abs(len(words_in_sent) - base_len) > (base_len * 0.25))
                
                sentence_map.append({
                    "id": i + 1, "text": s, "words": word_objects, 
                    "is_outlier": bool(sent_has_shift or is_outlier)
                })

            # 3. Final Determination & Internet Layer
            max_web_sim = 0.0
            best_url = "No source found"
            if highest_local_score < 0.90:
                links = await get_internet_resources(input_clean[:150], num_results=2)
                for url in links:
                    try:
                        content = await scrape_url_content(url)
                        if content:
                            web_vec = self.vectorizer.transform([content])
                            web_vec_1d = web_vec.toarray().flatten() if hasattr(web_vec, 'toarray') else web_vec.flatten()
                            
                            # Check dimension compatibility
                            if len(input_vec_1d) != len(web_vec_1d):
                                print(f"⚠️ Web vector has incompatible dimensions: input={len(input_vec_1d)}, web={len(web_vec_1d)}")
                                continue
                            
                            sim = float(cosine_similarity(input_vec.reshape(1,-1), web_vec.reshape(1,-1))[0][0])
                            if sim > max_web_sim:
                                max_web_sim, best_url = sim, url
                    except Exception as e:
                        print(f"⚠️ Error processing web content from {url}: {e}")
                        continue

            final_score = max(highest_local_score, max_web_sim)
            if final_score < 0.40:
                final_url = "Unique Sinhala text"
            elif highest_local_score >= max_web_sim:
                final_url = "Internal Database Match (Previous Student Submission)"
            else:
                final_url = best_url

            # 4. SAVE LAST
            if highest_local_score < 0.95:
                self.db.save_new_submission(input_text, pickle.dumps(input_vec))

            return {
                "ratio_data": {
                    "style_change_ratio": round((flagged_words / len(all_words)) * 100, 2) if all_words else 0,
                    "matched_url": final_url,
                    "similarity_score": round(final_score * 100, 2),
                    "sentence_map": sentence_map
                }
            }
        except Exception as e:
            print(f"❌ Engine Error: {e}")
            import traceback
            traceback.print_exc()
            return {"ratio_data": {"style_change_ratio": 0, "matched_url": f"Error: {str(e)}", "sentence_map": []}}