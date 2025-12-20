import joblib
import numpy as np
import re
from feature_extractor import SinhalaStylometryExtractor
from db_manager import DBManager 
# IMPORT YOUR NEW MODULE
from extrinsic_check import ExtrinsicAnalyzer

class PlagiarismPredictor:
    def __init__(self):
        self.model = joblib.load('plagiarism_model.pkl')
        self.extractor = SinhalaStylometryExtractor()
        self.db = DBManager()
        # Initialize the Idea Matcher
        self.extrinsic = ExtrinsicAnalyzer()

    def run_full_scan(self, student_text, internet_reference=None):
        """
        Performs both Intrinsic (Style) and Extrinsic (Idea) analysis.
        """
        print("\n" + "="*60)
        print("🚀 STARTING HYBRID SINHALA PLAGIARISM SCAN")
        print("="*60)

        # 1. INTRINSIC STYLE CHECK (What we did before)
        style_data = self.extractor.analyze_style(student_text)
        vector = np.array([[
            style_data['avg_sentence_length'],
            style_data['vocabulary_richness'],
            style_data['punctuation_density']
        ]])
        
        style_pred = self.model.predict(vector)[0]
        style_label = "Simple/Student" if style_pred == 1 else "Complex/Academic"

        print(f"STYLOMETRIC RESULT: Document style is '{style_label}'")

        # 2. EXTRINSIC IDEA CHECK (The New Step)
        idea_match_percentage = 0.0
        if internet_reference:
            idea_match_percentage = self.extrinsic.compare_idea(student_text, internet_reference)

        # 3. FUSION ENGINE (Combining results for final decision)
        # Higher confidence if BOTH style and idea indicate plagiarism
        is_plagiarized = False
        if idea_match_percentage > 50 or (style_pred == 0 and idea_match_percentage > 30):
            is_plagiarized = True

        final_report = {
            "style_analysis": style_label,
            "idea_match": f"{idea_match_percentage}%",
            "final_decision": "PLAGIARIZED" if is_plagiarized else "ORIGINAL"
        }

        # 4. SAVE TO DB
        self.db.save_plagiarism_log(
            student_text, 
            {"prediction": final_report['final_decision'], "confidence": final_report['idea_match']},
            style_data
        )

        return final_report

# --- HYBRID TEST AREA ---
if __name__ == "__main__":
    predictor = PlagiarismPredictor()

    # TEST SCENARIO: 
    # Student text uses simple Sinhala words but the SAME IDEA as the Internet
    student_text = "ලංකාවේ සල්ලි ප්‍රශ්න නිසා රජය අලුත් බදු ගහලා තියෙනවා."
    internet_text = "ශ්‍රී ලංකාවේ පවතින ආර්ථික අර්බුදය හේතුවෙන් රජය විසින් නව බදු ප්‍රතිසංස්කරණ හඳුන්වා දී ඇත."

    report = predictor.run_full_scan(student_text, internet_text)
    
    print("\n" + "*"*60)
    print(f"FINAL VIVA REPORT")
    print(f"Decision: {report['final_decision']}")
    print(f"Idea Similarity: {report['idea_match']}")
    print("*"*60)