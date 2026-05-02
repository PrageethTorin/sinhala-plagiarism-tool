import os
import asyncio
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from wsa_web_scraper import get_internet_resources, scrape_url_content, clean_text


class WSAAnalyzer:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.vectorizer = joblib.load(os.path.join(current_dir, "vectorizer.pkl"))

    def calculate_ttr(self, text: str) -> float:
        """Calculates Type-Token Ratio for lexical richness."""
        words = text.split()
        if not words:
            return 0.0
        return (len(set(words)) / len(words)) * 100.0

    def split_sentences(self, text: str):
        return [s.strip() for s in text.split(".") if len(s.strip()) > 5]

    def safe_similarity(self, a: float, b: float) -> float:
        if a == 0 and b == 0:
            return 100.0
        if max(a, b) == 0:
            return 0.0
        return (min(a, b) / max(a, b)) * 100.0

    async def compare_texts(self, source_text: str, student_text: str):
        source_text = (source_text or "").strip()
        student_text = (student_text or "").strip()

        if not source_text or not student_text:
            return {
                "ratio_data": {
                    "style_change_ratio": 0.0,
                    "matched_url": "No source found",
                    "similarity_score": 0.0,
                    "sentence_map": [],
                }
            }

        # Split student text into sentences for response mapping
        student_sentences = self.split_sentences(student_text)
        if not student_sentences:
            return {
                "ratio_data": {
                    "style_change_ratio": 0.0,
                    "matched_url": "No source found",
                    "similarity_score": 0.0,
                    "sentence_map": [],
                }
            }

        # Build source style profile
        source_sentences = self.split_sentences(source_text)

        source_avg_len = np.mean([len(s.split()) for s in source_sentences]) if source_sentences else len(source_text.split())
        source_avg_ttr = np.mean([self.calculate_ttr(s) for s in source_sentences]) if source_sentences else self.calculate_ttr(source_text)

        # Sentence-level mapping against source profile
        sentence_map = []
        similarity_scores = []
        flagged_count = 0

        for i, sentence in enumerate(student_sentences):
            curr_len = len(sentence.split())
            curr_ttr = self.calculate_ttr(sentence)

            len_sim = self.safe_similarity(curr_len, source_avg_len)
            ttr_sim = self.safe_similarity(curr_ttr, source_avg_ttr)

            sent_style_sim = (0.5 * len_sim) + (0.5 * ttr_sim)
            similarity_scores.append(sent_style_sim)

            is_outlier = sent_style_sim < 70.0
            if is_outlier:
                flagged_count += 1

            sentence_map.append({
                "id": i + 1,
                "text": sentence,
                "length": int(curr_len),
                "lexical_ttr": float(round(curr_ttr, 2)),
                "is_outlier": bool(is_outlier),
            })

        # Overall pairwise style similarity between source and student
        source_clean = clean_text(source_text)
        student_clean = clean_text(student_text)

        pairwise_sim = 0.0
        try:
            src_vec = self.vectorizer.transform([source_clean])
            stu_vec = self.vectorizer.transform([student_clean])
            pairwise_sim = float(cosine_similarity(src_vec, stu_vec)[0][0]) * 100.0
        except Exception:
            pairwise_sim = 0.0

        # Blend sentence-style similarity with vector similarity
        avg_sentence_style_sim = float(np.mean(similarity_scores)) if similarity_scores else 0.0
        final_similarity = round((0.6 * avg_sentence_style_sim) + (0.4 * pairwise_sim), 2)

        # Style change ratio = how much student style deviates from source style
        style_ratio = round(100.0 - final_similarity, 2)

        # Optional web discovery layer for metadata only
        links = []
        try:
            links = await get_internet_resources(student_clean[:150], num_results=5)
        except Exception:
            links = []

        best_url = "No source found"
        max_web_sim = 0.0

        student_vec = None
        try:
            student_vec = self.vectorizer.transform([student_clean])
        except Exception:
            student_vec = None

        if student_vec is not None:
            for url in links:
                try:
                    web_text = await asyncio.wait_for(scrape_url_content(url), timeout=30)
                    if web_text:
                        web_clean = clean_text(web_text)
                        web_vec = self.vectorizer.transform([web_clean])
                        sim = float(cosine_similarity(student_vec, web_vec)[0][0])
                        if sim > max_web_sim:
                            max_web_sim = sim
                            best_url = url
                except Exception:
                    continue

        matched_url = best_url if max_web_sim >= 0.45 else "No source found"

        return {
            "ratio_data": {
                "style_change_ratio": style_ratio,
                "matched_url": matched_url,
                "similarity_score": final_similarity,
                "sentence_map": sentence_map,
            }
        }