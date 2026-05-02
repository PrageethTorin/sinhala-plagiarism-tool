import os
import joblib
import numpy as np
import pickle
import re
from sklearn.metrics.pairwise import cosine_similarity
from .wsa_web_scraper import get_internet_resources, scrape_url_content, clean_text
from .extractor import StyleExtractor
from .db_bridge import DBBridge
from .synonym_map import get_synonyms  # Essential for the panel's "popped" suggestion requirement

class WSAAnalyzer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Load pre-trained TF-IDF vectorizer for semantic mapping
        self.vectorizer = joblib.load(os.path.join(current_dir, 'vectorizer.pkl'))
        self.extractor = StyleExtractor()
        self.db = DBBridge()

    def calculate_ttr(self, text):
        """Calculates Type-Token Ratio for lexical richness profiling."""
        words = text.split()
        if not words: return 0
        return (len(set(words)) / len(words)) * 100

    def split_sentences_preserve_punctuation(self, text):
        """Split text into sentences while keeping ending punctuation marks."""
        if not text:
            return []
        chunks = re.findall(r'[^.!?…]+[.!?…]*', text, flags=re.UNICODE)
        return [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

    def tokenize_sentence_preserve_format(self, sentence):
        """Tokenize sentence preserving punctuation and original spacing."""
        # Each token keeps trailing spaces, so frontend renders original formatting.
        return re.findall(r'\S+\s*', sentence, flags=re.UNICODE)

    def normalize_token_for_analysis(self, token):
        """Return clean lexical word for style detection/synonym lookup."""
        clean = re.sub(r'^[^\w\u0D80-\u0DFF]+|[^\w\u0D80-\u0DFF]+$', '', token, flags=re.UNICODE)
        return clean.strip()

    async def check_text(self, input_text):
        """
        Main analysis pipeline updated for interactive word replacement.
        1. Checks local history -> 2. Stylistic Analysis -> 3. Fetches Synonyms.
        """
        try:
            # 1. Local Database Collusion Check (PRE-SAVE)
            previous_submissions = self.db.get_all_previous_submissions()
            highest_local_score = 0.0
            matched_db_id = None
            matched_db_text = ""
            input_clean = clean_text(input_text)
            input_vec = self.vectorizer.transform([input_clean])
            
            # Convert to 1D for dimension safety checks
            input_vec_1d = input_vec.toarray().flatten() if hasattr(input_vec, 'toarray') else input_vec.flatten()

            for db_id, db_text, prev_vec_blob in previous_submissions:
                try:
                    prev_vec = pickle.loads(prev_vec_blob)
                    prev_vec_1d = prev_vec.toarray().flatten() if hasattr(prev_vec, 'toarray') else prev_vec.flatten()
                    
                    # Dimension compatibility check to prevent server crash
                    if len(input_vec_1d) != len(prev_vec_1d):
                        continue
                    
                    # Reshape for 2D comparison logic
                    sim = float(cosine_similarity(input_vec.reshape(1,-1), prev_vec.reshape(1,-1))[0][0])
                    if sim > highest_local_score:
                        highest_local_score = sim
                        matched_db_id = db_id
                        matched_db_text = db_text[:200]  # Store first 200 chars for display
                except Exception:
                    continue

            # 2. Stylistic & Morphological Analysis
            sentences = [s for s in self.split_sentences_preserve_punctuation(input_text) if len(s.strip()) > 5]
            if not sentences:
                return {"ratio_data": {"style_change_ratio": 0, "matched_url": "No source found", "sentence_map": []}}

            # Whole-text sentence length baseline
            sentence_lengths = [len(re.findall(r'\S+', s, flags=re.UNICODE)) for s in sentences]
            avg_sentence_len = float(np.mean(sentence_lengths)) if sentence_lengths else 0.0
            outlier_tolerance = max(2.0, avg_sentence_len * 0.25)
            
            sentence_map = []
            flagged_words_count = 0
            all_words_in_doc = input_text.split()
            avg_word_len = np.mean([len(w) for w in all_words_in_doc]) if all_words_in_doc else 5.0

            for i, s_text in enumerate(sentences):
                tokens_in_sent = self.tokenize_sentence_preserve_format(s_text)
                word_count_in_sent = len(re.findall(r'\S+', s_text, flags=re.UNICODE))
                word_objects = []

                for token in tokens_in_sent:
                    analysis_word = self.normalize_token_for_analysis(token)

                    # Skip pure punctuation tokens
                    if not analysis_word:
                        word_objects.append({
                            "text": token,
                            "replace_target": "",
                            "is_style_shift": False,
                            "suggestions": []
                        })
                        continue

                    # Detect if word uses expert academic morphology
                    is_shift = self.extractor.is_word_a_style_shift(analysis_word, avg_word_len)
                    
                    if is_shift:
                        flagged_words_count += 1
                    
                    # PANEL REQUIREMENT: Fetch suggestions for hover-popped replacement
                    word_suggestions = get_synonyms(analysis_word) if is_shift else []
                    
                    word_objects.append({
                        "text": token,
                        "replace_target": analysis_word,
                        "is_style_shift": is_shift,
                        "suggestions": word_suggestions  # For hover popover
                    })

                # Sentence level rule:
                # underline only when sentence is meaningfully higher than average
                is_high_length_sentence = bool(word_count_in_sent > (avg_sentence_len + outlier_tolerance))
                
                sentence_map.append({
                    "id": i + 1, 
                    "text": s_text, 
                    "words": word_objects, 
                    "is_outlier": is_high_length_sentence,
                    "should_underline": is_high_length_sentence
                })

            # 3. Final Determination & Internet Layer
            max_web_sim = 0.0
            best_url = "No source found"
            web_candidate_url = ""
            
            # Only search internet if no high-match local database collusion is found
            if highest_local_score < 0.90:
                links = await get_internet_resources(input_clean[:150], num_results=2)
                if links:
                    web_candidate_url = links[0]
                for url in links:
                    try:
                        content = await scrape_url_content(url)
                        if content:
                            web_vec = self.vectorizer.transform([content])
                            web_vec_1d = web_vec.toarray().flatten() if hasattr(web_vec, 'toarray') else web_vec.flatten()
                            
                            if len(input_vec_1d) == len(web_vec_1d):
                                sim = float(cosine_similarity(input_vec.reshape(1,-1), web_vec.reshape(1,-1))[0][0])
                                if sim > max_web_sim:
                                    max_web_sim, best_url = sim, url
                    except Exception:
                        continue

            # Determine final source and status
            final_score = max(highest_local_score, max_web_sim)
            match_type = "unique"
            if final_score < 0.40:
                final_url = "Unique Sinhala text"
                match_type = "unique"
            elif highest_local_score >= max_web_sim:
                final_url = f"Internal Database Match - DB ID: {matched_db_id}"
                match_type = "internal"
            else:
                final_url = best_url
                match_type = "web"

            # 4. SAVE NEW FINGERPRINT LAST
            if highest_local_score < 0.95:
                self.db.save_new_submission(input_text, pickle.dumps(input_vec))

            # Return final stylometric analytics
            return {
                "ratio_data": {
                    "style_change_ratio": round((flagged_words_count / len(all_words_in_doc)) * 100, 2) if all_words_in_doc else 0,
                    "matched_url": final_url,
                    "similarity_score": round(final_score * 100, 2),
                    "web_matched_url": best_url if best_url.startswith("http") else web_candidate_url,
                    "web_similarity_score": round(max_web_sim * 100, 2),
                    "sentence_map": sentence_map,
                    "match_type": match_type,
                    "matched_db_id": matched_db_id,
                    "matched_text": matched_db_text
                }
            }
        except Exception as e:
            print(f"❌ Engine Error: {e}")
            import traceback
            traceback.print_exc()
            return {"ratio_data": {"style_change_ratio": 0, "matched_url": f"Error: {str(e)}", "sentence_map": []}}