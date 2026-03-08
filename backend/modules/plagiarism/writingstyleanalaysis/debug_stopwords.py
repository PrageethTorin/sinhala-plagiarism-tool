# backend/debug_stopwords.py
from modules.ParaphraseDetection.preprocessor import preprocess_text, load_stop_words, normalize_sinhala

# 1. The word we WANT to remove
target_word = "විසින්" 
normalized_target = normalize_sinhala(target_word)

print(f"--- DEBUGGING '{target_word}' ---")

# 2. Check the Sentence
text = "ගුරුතුමා විසින් පාඩම"
tokens = preprocess_text(text)
print(f"\n1. Tokens in sentence: {tokens}")

# Find 'visin' in tokens
token_visin = next((t for t in tokens if "විසින්" in t), None)
if token_visin:
    print(f"   -> Token found: '{token_visin}'")
    print(f"   -> Token Bytes: {list(token_visin.encode('utf-8'))}")
else:
    print("   -> 'විසින්' not found in tokens??")

# 3. Check the Stop Word File
print("\n2. Checking Stop Words File...")
stop_words = load_stop_words()

if normalized_target in stop_words:
    print(f"   ✅ SUCCESS: '{target_word}' IS in the stop word list.")
else:
    print(f"   ❌ FAILURE: '{target_word}' is NOT in the list.")
    
    # Let's print the first few words to see what they look like
    print("\n   Here are the first 5 words in your file (Bytes):")
    for i, word in enumerate(list(stop_words)[:5]):
        print(f"   {i+1}. {word} : {list(word.encode('utf-8'))}")

print("\n--------------------------------")