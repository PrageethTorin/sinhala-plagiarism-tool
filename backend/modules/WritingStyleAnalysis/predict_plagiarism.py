import joblib
import numpy as np
import os
from feature_extractor import SinhalaStylometryExtractor

class PlagiarismPredictor:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model = joblib.load(os.path.join(current_dir, 'plagiarism_model.pkl'))
        self.extractor = SinhalaStylometryExtractor()
        self.class_map = {
            0: "LITERARY / ACADEMIC", 1: "SPOKEN / NATURAL",
            2: "🚨 SUSPICIOUS: PARAPHRASED", 3: "🚨 SUSPICIOUS: MOSAIC"
        }

    def run_analysis(self, sentences_list):
        print("\n--- INTRINSIC STYLE SCAN START ---")
        results = []
        for i, sentence in enumerate(sentences_list, 1):
            feats = self.extractor.analyze_style(sentence)
            vec = np.array([list(feats.values())], dtype=float)
            prediction = self.model.predict(vec)[0]
            label = self.class_map[prediction]
            results.append(prediction)
            print(f"Sentence {i}: [{label}] | Length: {feats['sentence_length']} | Bias: {feats['linguistic_bias']}")

        is_suspicious = len(set(results)) > 1
        print("="*75)
        print(f"FINAL DECISION: {'🚨 SUSPICIOUS' if is_suspicious else '✅ CONSISTENT'}")
        print("="*75 + "\n")

if __name__ == "__main__":
    scanner = PlagiarismPredictor()
    user_examples = [
        "මම ඊයේ ගෙදර යනවිට ලොකු ගොඩනැගිල්ලක් දුටුවෙමි.",
        "මම ඊයේ ගෙදර යන විට ඉතා විශාල සංකීර්ණ ගණයේ ගොඩනැගිල්ලක් දුටුවෙමි."
    ]
    scanner.run_analysis(user_examples)