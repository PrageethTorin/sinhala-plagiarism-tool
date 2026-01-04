# Sinhala Semantic Similarity - Algorithm Documentation

## Overview

This document describes the algorithms used in the Sinhala Semantic Similarity component of the plagiarism detection system. The system uses a **Hybrid Approach** that combines custom statistical algorithms with machine learning models for optimal accuracy.

---

## 1. System Architecture

```
Input Text Pair (Text1, Text2)
         │
         ▼
┌─────────────────────────────────────┐
│     STEP 1: CUSTOM ALGORITHM        │
│     (Always executed first)         │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ Jaccard Similarity    (40%)  │  │
│  │ 2-gram Similarity     (20%)  │  │
│  │ 3-gram Similarity     (20%)  │  │
│  │ Word Order Similarity (20%)  │  │
│  └───────────────────────────────┘  │
│              │                      │
│              ▼                      │
│     custom_score = weighted_sum     │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│     STEP 2: CASE CLASSIFICATION     │
│                                     │
│  IF custom_score < 0.4:             │
│     → EASY NEGATIVE (Not Similar)   │
│     → Return custom_score           │
│                                     │
│  IF custom_score > 0.7:             │
│     → EASY POSITIVE (Similar)       │
│     → Return custom_score           │
│                                     │
│  IF 0.4 ≤ custom_score ≤ 0.7:       │
│     → DIFFICULT CASE                │
│     → Proceed to Step 3             │
└─────────────────────────────────────┘
              │
              ▼ (Only for difficult cases)
┌─────────────────────────────────────┐
│   STEP 3: EMBEDDING-BASED MODEL     │
│                                     │
│  Model: Fine-tuned MiniLM-L12-v2    │
│                                     │
│  embed1 = encode(text1)             │
│  embed2 = encode(text2)             │
│  embedding_score = cosine(e1, e2)   │
│                                     │
│  final_score = (custom + embed) / 2 │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│          OUTPUT                     │
│                                     │
│  - similarity_score (0.0 - 1.0)     │
│  - verdict (Original/Suspected/     │
│             Plagiarized)            │
│  - confidence level                 │
│  - component breakdown              │
│  - method used                      │
└─────────────────────────────────────┘
```

---

## 2. Custom Algorithms (Statistical Methods)

### 2.1 Jaccard Similarity (Weight: 40%)

**Purpose:** Measures word-level overlap between two texts.

**Formula:**
```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

Where:
- A = set of words in text1 (after preprocessing)
- B = set of words in text2 (after preprocessing)

**Implementation:**
```python
def jaccard_similarity(text1, text2):
    set1 = set(preprocess(text1))  # Tokenize, remove stopwords
    set2 = set(preprocess(text2))

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0
```

**Characteristics:**
- Range: 0.0 (no overlap) to 1.0 (identical sets)
- Fast computation
- Word order independent
- Sensitive to synonyms (treats synonyms as different words)

---

### 2.2 N-gram Similarity (Weight: 20% for 2-gram, 20% for 3-gram)

**Purpose:** Captures character-level patterns and partial word matches.

**Formula:**
```
NGram(A, B, n) = |ngrams(A, n) ∩ ngrams(B, n)| / |ngrams(A, n) ∪ ngrams(B, n)|
```

Where `ngrams(text, n)` extracts all character sequences of length n.

**Implementation:**
```python
def get_ngrams(text, n):
    text = remove_spaces(text)
    return [text[i:i+n] for i in range(len(text) - n + 1)]

def ngram_similarity(text1, text2, n=3):
    ngrams1 = set(get_ngrams(text1, n))
    ngrams2 = set(get_ngrams(text2, n))

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    return intersection / union if union > 0 else 0.0
```

**Why 2-gram and 3-gram:**
- **2-gram (bigrams):** Captures adjacent character pairs
  - Good for detecting morphological variations
  - Example: "ගමන" → ["ගම", "මන"]
- **3-gram (trigrams):** Captures character triplets
  - More specific pattern matching
  - Less false positives
  - Example: "ගමන" → ["ගමන"]

**Sinhala-specific considerations:**
- Sinhala uses conjunct consonants (e.g., "ක්‍ර")
- Character n-grams capture sub-syllable patterns
- Helps detect slightly modified words

---

### 2.3 Word Order Similarity (Weight: 20%)

**Purpose:** Measures how similarly words are ordered in both texts.

**Algorithm:**
1. Find common words between texts
2. Get position of each common word in both texts
3. Calculate average position difference
4. Normalize to 0-1 range

**Implementation:**
```python
def word_order_similarity(text1, text2):
    tokens1 = preprocess(text1)
    tokens2 = preprocess(text2)

    common = set(tokens1) & set(tokens2)
    if len(common) < 2:
        return 0.5  # Neutral for few common words

    pos1 = {word: i for i, word in enumerate(tokens1) if word in common}
    pos2 = {word: i for i, word in enumerate(tokens2) if word in common}

    diffs = [abs(pos1[w] - pos2[w]) for w in common if w in pos1 and w in pos2]

    avg_diff = sum(diffs) / len(diffs)
    max_possible = max(len(tokens1), len(tokens2))

    return 1 - (avg_diff / max_possible)
```

**Characteristics:**
- Detects sentence restructuring
- Handles word reordering in paraphrases
- Returns 0.5 (neutral) when insufficient common words

---

## 3. Hybrid Score Calculation

### 3.1 Weighted Combination

```python
weights = {
    'jaccard': 0.4,      # 40% - Word overlap
    'ngram_2': 0.2,      # 20% - Bigram patterns
    'ngram_3': 0.2,      # 20% - Trigram patterns
    'word_order': 0.2    # 20% - Structural similarity
}

custom_score = (
    weights['jaccard'] * jaccard_similarity(t1, t2) +
    weights['ngram_2'] * ngram_similarity(t1, t2, n=2) +
    weights['ngram_3'] * ngram_similarity(t1, t2, n=3) +
    weights['word_order'] * word_order_similarity(t1, t2)
)
```

### 3.2 Weight Justification

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Jaccard | 40% | Primary indicator of content overlap |
| 2-gram | 20% | Catches morphological variations |
| 3-gram | 20% | Precise pattern matching |
| Word Order | 20% | Detects restructuring plagiarism |

---

## 4. Case Classification

### 4.1 Thresholds

| Score Range | Classification | Action |
|-------------|----------------|--------|
| < 0.4 | Easy Negative | Use custom score only |
| > 0.7 | Easy Positive | Use custom score only |
| 0.4 - 0.7 | Difficult | Combine with ML model |

### 4.2 Rationale

**Why this approach:**
1. **Efficiency:** ML model is computationally expensive
2. **Accuracy:** Custom algorithms are reliable for extreme cases
3. **Research validity:** Demonstrates hybrid methodology

**Threshold selection:**
- 0.4: Below this, texts are clearly different
- 0.7: Above this, texts are clearly similar
- Middle range: Requires deeper semantic analysis

---

## 5. Machine Learning Component

### 5.1 Base Model

**Model:** `paraphrase-multilingual-MiniLM-L12-v2`

**Architecture:**
- 12 transformer layers
- 384 embedding dimensions
- Supports 50+ languages including Sinhala
- Pre-trained on paraphrase detection

### 5.2 Fine-tuning

**Dataset:** Sinhala sentence pairs with similarity labels

**Training Configuration:**
```python
{
    "base_model": "paraphrase-multilingual-MiniLM-L12-v2",
    "epochs": 3,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "warmup_steps": 100,
    "loss_function": "CosineSimilarityLoss"
}
```

### 5.3 Embedding Similarity

```python
def embedding_similarity(text1, text2, model):
    embeddings = model.encode([text1, text2])

    # Cosine similarity
    similarity = cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0]

    return float(similarity)
```

---

## 6. Final Score Combination (Difficult Cases)

For cases where 0.4 ≤ custom_score ≤ 0.7:

```python
final_score = (custom_score + embedding_score) / 2
```

**Why equal weighting:**
- Both methods contribute equally
- Custom captures lexical similarity
- Embedding captures semantic similarity
- Average balances both perspectives

---

## 7. Sinhala Text Preprocessing

### 7.1 Pipeline

```python
def preprocess(text):
    # 1. Unicode normalization
    text = normalize_unicode(text)

    # 2. Remove punctuation (keep Sinhala characters)
    text = re.sub(r'[^\w\s\u0D80-\u0DFF]', ' ', text)

    # 3. Tokenize
    tokens = text.split()

    # 4. Remove stopwords
    tokens = [t for t in tokens if t not in SINHALA_STOPWORDS]

    # 5. Remove short tokens
    tokens = [t for t in tokens if len(t) > 1]

    return tokens
```

### 7.2 Sinhala Stopwords

```python
SINHALA_STOPWORDS = {
    # Pronouns
    'මම', 'ඔබ', 'එය', 'අප', 'ඔවුන්', 'ඔහු', 'ඇය',

    # Conjunctions
    'සහ', 'නමුත්', 'හෝ',

    # Demonstratives
    'ඒ', 'මෙය', 'එහි', 'මෙහි', 'එම', 'මෙම',

    # Question words
    'කොහේ', 'කවුද', 'මොකද', 'කොහොමද', 'කවදා', 'කොහෙන්',

    # Other function words
    'මට', 'එවිට', 'මෙවිට', 'එසේ', 'මෙසේ'
}
```

### 7.3 Sinhala Character Range

- Unicode range: U+0D80 to U+0DFF
- Includes vowels, consonants, and modifiers
- Special handling for conjuncts (hal + consonant)

---

## 8. Verdict Classification

| Final Score | Verdict | Confidence |
|-------------|---------|------------|
| ≥ 0.8 | Plagiarized | High |
| 0.6 - 0.8 | Suspected Plagiarism | Medium |
| 0.4 - 0.6 | Needs Review | Low |
| < 0.4 | Original | High |

---

## 9. Performance Characteristics

### 9.1 Time Complexity

| Component | Complexity | Typical Time |
|-----------|------------|--------------|
| Jaccard | O(n + m) | ~1ms |
| N-gram | O(n + m) | ~2ms |
| Word Order | O(n * m) | ~3ms |
| Custom Total | - | ~10ms |
| Embedding | O(n) | ~100ms |
| Hybrid (difficult) | - | ~110ms |

Where n, m = lengths of input texts

### 9.2 Accuracy Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Precision | > 0.85 | Minimize false positives |
| Recall | > 0.80 | Catch actual plagiarism |
| F1 Score | > 0.82 | Balanced performance |
| ROC-AUC | > 0.90 | Overall discrimination |

---

## 10. API Usage

### 10.1 Basic Request

```json
POST /api/supervisor-hybrid
{
    "text_pair": {
        "original": "ශ්‍රී ලංකාව දූපතක් වේ",
        "suspicious": "ලංකාව යනු දූපතකි"
    },
    "threshold": 0.5
}
```

### 10.2 Response

```json
{
    "similarity_score": 0.72,
    "is_plagiarized": true,
    "verdict": "Suspected Plagiarism",
    "confidence": 0.85,
    "method_used": "hybrid_fine_tuned",
    "components": {
        "custom_score": 0.65,
        "embedding_score": 0.79,
        "jaccard": 0.60,
        "ngram_2": 0.55,
        "ngram_3": 0.48,
        "word_order": 0.70
    }
}
```

---

## 11. References

1. Jaccard, P. (1912). "The distribution of the flora in the alpine zone"
2. Kondrak, G. (2005). "N-Gram Similarity and Distance"
3. Reimers, N. & Gurevych, I. (2019). "Sentence-BERT"
4. Conneau, A. et al. (2020). "Unsupervised Cross-lingual Representation Learning"

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial implementation |
| 1.1 | Dec 2024 | Added hybrid routing |
| 1.2 | Dec 2024 | Fine-tuned model integration |

---

*Document maintained by: S N S Dahanayake (IT22920522)*
*Last updated: December 2024*
