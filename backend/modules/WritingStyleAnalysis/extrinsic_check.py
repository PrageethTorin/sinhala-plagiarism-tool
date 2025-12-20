import numpy as np
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ExtrinsicAnalyzer:
    def __init__(self, stopword_path='../../stopwords_sinhala.txt'):
        self.stopword_path = stopword_path
        self.stop_words = self.load_stopwords()

    def load_stopwords(self):
        """Loads the Sinhala stopwords you already have in the backend folder"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, self.stopword_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Stopword Load Warning: {e}")
            return []

    def get_clean_tokens(self, text):
        """Removes symbols and stopwords to isolate the 'Core Idea'"""
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        # Filter tokens
        clean_words = [w for w in words if w not in self.stop_words]
        return " ".join(clean_words)

    def compare_idea(self, student_text, internet_text):
        """Compares two texts to see if the 'Idea' is the same even if words changed"""
        
        # 1. Isolate the 'Idea' (Tokens)
        student_idea = self.get_clean_tokens(student_text)
        internet_idea = self.get_clean_tokens(internet_text)

        if not student_idea or not internet_idea:
            return 0.0

        # 2. Tokenization & Vectorization (The Supervisor's method)
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([student_idea, internet_idea])

        # 3. Calculate Similarity Score
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        percentage = round(score * 100, 2)
        
        print("\n" + "="*50)
        print(f"🔬 RESEARCH COMPONENT: EXTRINSIC IDEA MATCH")
        print("="*50)
        print(f"Similarity Score: {percentage}%")
        
        if percentage > 45:
             print("🚨 ALERT: Paraphrased Plagiarism Detected (Same Idea).")
        else:
             print("✅ PASS: The content appears original.")
        print("="*50 + "\n")
        
        return percentage

# --- VIVA DEMONSTRATION AREA ---
if __name__ == "__main__":
    analyzer = ExtrinsicAnalyzer()

    # TEST CASE: Student changed formal words to simple words but kept the IDEA
    # Student uses: 'සල්ලි ප්‍රශ්න' (money problems), 'බදු ගහලා' (put taxes)
    student_work = "ලංකාවේ සල්ලි ප්‍රශ්න නිසා රජය අලුත් බදු ගහලා තියෙනවා. ඒක ලොකු ප්‍රශ්නයක්."

    # Internet Source uses: 'ආර්ථික අර්බුදය' (economic crisis), 'ප්‍රතිසංස්කරණ' (reforms)
    internet_source = "ශ්‍රී ලංකාවේ පවතින ආර්ථික අර්බුදය හේතුවෙන් රජය විසින් නව බදු ප්‍රතිසංස්කරණ හඳුන්වා දී ඇත."

    analyzer.compare_idea(student_work, internet_source)