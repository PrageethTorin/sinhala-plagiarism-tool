"""
Expand Training Dataset using Crawled Wikipedia Corpus
Target: 2000+ training pairs with diverse similarity levels
"""

import os
import sys
import sqlite3
import random
import pandas as pd
from typing import List, Dict, Tuple

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(BASE_DIR)
CORPUS_DB = os.path.join(MODULE_DIR, "corpus", "sinhala_corpus.db")
OUTPUT_FILE = os.path.join(BASE_DIR, "sinhala_similarity_train_expanded.csv")

# Target counts
TARGET_TOTAL = 2500
IDENTITY_RATIO = 0.10      # 10% - exact copies (label=1.0)
SAME_TOPIC_RATIO = 0.25    # 25% - same category pairs (label=0.6-0.85)
CROSS_TOPIC_RATIO = 0.40   # 40% - different categories (label=0.0-0.3)
PARTIAL_RATIO = 0.25       # 25% - partial overlap (label=0.3-0.6)


def load_corpus_by_category() -> Dict[str, List[str]]:
    """Load paragraphs grouped by category from crawler database"""
    if not os.path.exists(CORPUS_DB):
        print(f"Corpus database not found: {CORPUS_DB}")
        return {}

    conn = sqlite3.connect(CORPUS_DB)
    cursor = conn.cursor()

    category_paragraphs = {}

    try:
        cursor.execute("""
            SELECT d.category, p.paragraph_text
            FROM paragraphs p
            JOIN documents d ON p.document_id = d.id
            WHERE p.char_count >= 80 AND p.char_count <= 500
        """)

        for row in cursor.fetchall():
            category = row[0] or "general"
            text = row[1].strip()

            if category not in category_paragraphs:
                category_paragraphs[category] = []
            category_paragraphs[category].append(text)

        print(f"Loaded paragraphs from {len(category_paragraphs)} categories")
        for cat, paras in list(category_paragraphs.items())[:5]:
            print(f"  {cat}: {len(paras)} paragraphs")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    conn.close()
    return category_paragraphs


def generate_identity_pairs(paragraphs: List[str], count: int) -> List[Dict]:
    """Generate exact copy pairs (label=1.0)"""
    pairs = []
    samples = random.sample(paragraphs, min(count, len(paragraphs)))

    for text in samples:
        pairs.append({
            "sentence_1": text,
            "sentence_2": text,
            "label": 1.0
        })

    return pairs


def generate_same_topic_pairs(category_paragraphs: Dict[str, List[str]], count: int) -> List[Dict]:
    """Generate pairs from same category (label=0.6-0.85)"""
    pairs = []
    categories = [c for c, p in category_paragraphs.items() if len(p) >= 5]

    for _ in range(count):
        if not categories:
            break

        cat = random.choice(categories)
        paras = category_paragraphs[cat]

        if len(paras) >= 2:
            s1, s2 = random.sample(paras, 2)
            # Same topic = moderate to high similarity
            label = random.uniform(0.55, 0.80)
            pairs.append({
                "sentence_1": s1,
                "sentence_2": s2,
                "label": round(label, 2)
            })

    return pairs


def generate_cross_topic_pairs(category_paragraphs: Dict[str, List[str]], count: int) -> List[Dict]:
    """Generate pairs from different categories (label=0.0-0.3)"""
    pairs = []
    categories = [c for c, p in category_paragraphs.items() if len(p) >= 3]

    for _ in range(count):
        if len(categories) < 2:
            break

        cat1, cat2 = random.sample(categories, 2)
        s1 = random.choice(category_paragraphs[cat1])
        s2 = random.choice(category_paragraphs[cat2])

        # Different topics = low similarity
        label = random.uniform(0.0, 0.25)
        pairs.append({
            "sentence_1": s1,
            "sentence_2": s2,
            "label": round(label, 2)
        })

    return pairs


def generate_partial_pairs(paragraphs: List[str], count: int) -> List[Dict]:
    """Generate partial overlap pairs (label=0.3-0.6)"""
    pairs = []

    for _ in range(count):
        if len(paragraphs) < 2:
            break

        text = random.choice(paragraphs)
        words = text.split()

        if len(words) < 10:
            continue

        # Method 1: Truncate sentence
        if random.random() < 0.5:
            cut_point = random.randint(len(words) // 3, 2 * len(words) // 3)
            modified = " ".join(words[:cut_point])
            label = 0.4 + (cut_point / len(words)) * 0.3
        else:
            # Method 2: Shuffle some words
            num_shuffle = random.randint(2, min(5, len(words) // 3))
            indices = random.sample(range(len(words)), num_shuffle)
            shuffled_words = words.copy()
            values = [words[i] for i in indices]
            random.shuffle(values)
            for i, idx in enumerate(indices):
                shuffled_words[idx] = values[i]
            modified = " ".join(shuffled_words)
            label = 0.65 - (num_shuffle / len(words)) * 0.3

        pairs.append({
            "sentence_1": text,
            "sentence_2": modified,
            "label": round(max(0.3, min(0.6, label)), 2)
        })

    return pairs


def load_existing_data() -> List[Dict]:
    """Load existing training pairs"""
    existing_files = [
        os.path.join(BASE_DIR, "sinhala_similarity_train_large.csv"),
        os.path.join(BASE_DIR, "sinhala_paraphrases.csv"),
    ]

    all_pairs = []

    for filepath in existing_files:
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                if 'sentence_1' in df.columns and 'sentence_2' in df.columns:
                    for _, row in df.iterrows():
                        all_pairs.append({
                            "sentence_1": str(row.get("sentence_1", "")),
                            "sentence_2": str(row.get("sentence_2", "")),
                            "label": float(row.get("label", 0.5))
                        })
                    print(f"Loaded {len(df)} pairs from {os.path.basename(filepath)}")
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

    return all_pairs


def main():
    print("=" * 60)
    print("TRAINING DATASET EXPANSION")
    print("=" * 60)

    # Load corpus by category
    category_paragraphs = load_corpus_by_category()

    if not category_paragraphs:
        print("No corpus data available!")
        return

    # Flatten paragraphs for some operations
    all_paragraphs = []
    for paras in category_paragraphs.values():
        all_paragraphs.extend(paras)

    print(f"\nTotal paragraphs available: {len(all_paragraphs)}")

    # Load existing training data
    existing_pairs = load_existing_data()
    print(f"Existing training pairs: {len(existing_pairs)}")

    # Calculate how many new pairs needed
    remaining = TARGET_TOTAL - len(existing_pairs)
    if remaining <= 0:
        print(f"\nAlready have {len(existing_pairs)} pairs. Target: {TARGET_TOTAL}")
        remaining = 500  # Add some anyway

    print(f"\nGenerating {remaining} new pairs...")

    # Generate new pairs
    new_pairs = []

    # Identity pairs
    identity_count = int(remaining * IDENTITY_RATIO)
    identity_pairs = generate_identity_pairs(all_paragraphs, identity_count)
    new_pairs.extend(identity_pairs)
    print(f"  Generated {len(identity_pairs)} identity pairs (label=1.0)")

    # Same topic pairs
    same_topic_count = int(remaining * SAME_TOPIC_RATIO)
    same_topic_pairs = generate_same_topic_pairs(category_paragraphs, same_topic_count)
    new_pairs.extend(same_topic_pairs)
    print(f"  Generated {len(same_topic_pairs)} same-topic pairs (label=0.55-0.80)")

    # Cross topic pairs
    cross_topic_count = int(remaining * CROSS_TOPIC_RATIO)
    cross_topic_pairs = generate_cross_topic_pairs(category_paragraphs, cross_topic_count)
    new_pairs.extend(cross_topic_pairs)
    print(f"  Generated {len(cross_topic_pairs)} cross-topic pairs (label=0.0-0.25)")

    # Partial overlap pairs
    partial_count = int(remaining * PARTIAL_RATIO)
    partial_pairs = generate_partial_pairs(all_paragraphs, partial_count)
    new_pairs.extend(partial_pairs)
    print(f"  Generated {len(partial_pairs)} partial-overlap pairs (label=0.3-0.6)")

    # Combine all pairs
    all_pairs = existing_pairs + new_pairs

    # Shuffle
    random.shuffle(all_pairs)

    # Save
    df = pd.DataFrame(all_pairs)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print("\n" + "=" * 60)
    print("DATASET EXPANSION COMPLETE")
    print("=" * 60)
    print(f"Total training pairs: {len(df)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nLabel distribution:")
    bins = [0, 0.3, 0.5, 0.7, 0.9, 1.01]
    labels_range = ['0.0-0.3 (dissimilar)', '0.3-0.5 (low)', '0.5-0.7 (medium)', '0.7-0.9 (high)', '0.9-1.0 (identical)']
    df['label_range'] = pd.cut(df['label'], bins=bins, labels=labels_range)
    print(df['label_range'].value_counts().sort_index())

    return True


if __name__ == "__main__":
    main()
