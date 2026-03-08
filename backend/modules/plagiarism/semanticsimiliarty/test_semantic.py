# test_semantic.py
from modules.ParaphraseDetection.semantic_analyzer import calculate_semantic_similarity

print("\n--- 🧠 Testing Semantic Analysis (AI Brain) ---")

# TEST 1: Different words, SAME meaning
# A: "The teacher taught the lesson"
# B: "The lesson was explained by the master"
text_A = "ගුරුතුමා පාඩම ඉගැන්නුවා"
text_B = "පාඩම ගුරුවරයා විසින් පැහැදිලි කරන ලදී"

print(f"\nExample 1 (Same Meaning):")
print(f"   A: {text_A}")
print(f"   B: {text_B}")
score1 = calculate_semantic_similarity(text_A, text_B)
print(f"   👉 Score: {score1:.4f}") 
# Expected: High score (above 0.7)

# TEST 2: Different words, DIFFERENT meaning
# A: "I went to school"
# B: "I ate rice"
text_C = "මම පාසල් ගියා"
text_D = "මම බත් කෑවා"

print(f"\nExample 2 (Different Meaning):")
print(f"   C: {text_C}")
print(f"   D: {text_D}")
score2 = calculate_semantic_similarity(text_C, text_D)
print(f"   👉 Score: {score2:.4f}")
# Expected: Low score (below 0.5)

print("\n-------------------------------------------")