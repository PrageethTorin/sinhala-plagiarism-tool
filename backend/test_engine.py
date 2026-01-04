# test_engine.py
from modules.ParaphraseDetection.plagiarism_engine import check_paraphrase

print("--- 🕵️ TESTING PARAPHRASE DETECTION COMPONENT ---")

# SCENARIO: A student copies a sentence but changes 'teacher' to 'lecturer' 
# and 'explained' to 'taught'.

# Original Source
source = "ගුරුතුමා විසින් සිසුන්ට පාඩම පැහැදිලි කරන ලදී."
# (The teacher explained the lesson to the students.)

# Suspicious Text (Paraphrased)
suspicious = "ආචාර්යවරයා ළමයින්ට පාඩම ඉගැන්නුවා."
# (The lecturer taught the lesson to the children.)

print(f"\nOriginal:   {source}")
print(f"Suspicious: {suspicious}")
print("-" * 50)

# Calling the renamed function 'check_paraphrase'
result = check_paraphrase(source, suspicious)

print(f"📊 Lexical Score (Words):     {result['lexical_score']}%")
print(f"🧠 Semantic Score (AI):       {result['semantic_score']}%")
print("=" * 40)
print(f"🏁 PARAPHRASE PROBABILITY:    {result['paraphrase_score']}%")
print(f"🚨 PARAPHRASE DETECTED?       {result['is_paraphrased']}")
print("=" * 40) 