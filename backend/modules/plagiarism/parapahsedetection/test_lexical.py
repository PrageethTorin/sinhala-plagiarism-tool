# test_lexical.py
from modules.ParaphraseDetection.lexical_analyzer import calculate_lexical_similarity

print("--- Testing with Valid Database Data ---")

# Sentence A: "Mava gedara giyaya" (Mother went home)
tokens_A = ['මව', 'ගෙදර', 'ගියාය']

# Sentence B: "Amma gedara giyaya" (Mother went home)
# We know 'මව' and 'අම්මා' are synonyms in your DB (ID: SY0001)
tokens_B = ['අම්මා', 'ගෙදර', 'ගියාය']

print(f"Sentence A: {tokens_A}")
print(f"Sentence B: {tokens_B}")

score = calculate_lexical_similarity(tokens_A, tokens_B)

print("-" * 30)
print(f"Similarity Score: {score:.4f}")
print("-" * 30)

# EXPECTED RESULT:
# Matches: 'ගෙදර' (Exact), 'ගියාය' (Exact), 'මව'=='අම්මා' (Synonym DB)
# Total Matches: 3
# Length: 3
# Score: 3/3 = 1.0