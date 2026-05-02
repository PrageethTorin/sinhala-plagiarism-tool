# test_preprocessing.py
from modules.ParaphraseDetection.preprocessor import preprocess_text

# Example Sentence: "The teacher explained the lesson by himself"
# 'විසින්' (by) is a common stop word you likely added.
text = "පරිසරය ආරක්ෂා කිරීම සඳහා අපි ගස් සිටුවිය යුතුය."

print("-" * 30)
print(f"Original Text: {text}")
print("-" * 30)

tokens = preprocess_text(text)

print(f"Cleaned Tokens: {tokens}")
print("-" * 30)