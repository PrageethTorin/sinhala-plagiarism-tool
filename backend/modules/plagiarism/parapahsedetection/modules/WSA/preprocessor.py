import re

class SinhalaPreprocessor:
    def __init__(self):
        # පොදු සිංහල නිපාත පද (Stopwords)
        self.stopwords = ["සහ", "හා", "මම", "අපි", "ඔහු", "ඇය", "එය", "මෙහි", "එහි"]

    def preprocess_sinhala(self, text):
        """වචන විශ්ලේෂණය සඳහා දත්ත පිරිසිදු කිරීම."""
        if not text: return ""
        # ඉංග්‍රීසි අකුරු සහ විශේෂ සංකේත ඉවත් කර සිංහල යුනිකෝඩ් පමණක් ඉතිරි කිරීම
        text = re.sub(r'[^\u0D80-\u0DFF\s]', '', str(text))
        return text.strip()

    def split_into_sentences(self, text):
        """ඡේදයක් වාක්‍යවලට වෙන් කිරීම (මෙය train_model.py සඳහා අත්‍යවශ්‍ය වේ)."""
        if not text: return []
        # සිංහල වාක්‍ය අවසාන වන ලකුණු අනුව වෙන් කිරීම
        sentences = re.split(r'[.|।|?|!]', str(text))
        # වචන 2කට වඩා වැඩි වාක්‍ය පමණක් ලබා ගැනීම
        return [s.strip() for s in sentences if len(s.strip().split()) > 2]