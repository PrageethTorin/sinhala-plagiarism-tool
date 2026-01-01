"""
Build FAISS Index from Crawled Sinhala Corpus
Uses paragraphs from Wikipedia crawler to build vector search index
"""

import os
import sys
import sqlite3
import numpy as np

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(BASE_DIR)
CORPUS_DB = os.path.join(BASE_DIR, "sinhala_corpus.db")
OUTPUT_DB = os.path.join(BASE_DIR, "corpus.db")
INDEX_PATH = os.path.join(BASE_DIR, "faiss_index.bin")
MODEL_PATH = os.path.join(MODULE_DIR, "sinhala_fine_tuned_model")
PARAGRAPHS_FILE = os.path.join(BASE_DIR, "corpus_paragraphs.txt")


def load_paragraphs_from_db():
    """Load paragraphs from the crawler database"""
    if not os.path.exists(CORPUS_DB):
        print(f"Corpus database not found: {CORPUS_DB}")
        return []

    conn = sqlite3.connect(CORPUS_DB)
    cursor = conn.cursor()

    paragraphs = []
    try:
        cursor.execute("SELECT content FROM paragraphs")
        rows = cursor.fetchall()
        paragraphs = [row[0] for row in rows if row[0] and len(row[0].strip()) > 30]
        print(f"Loaded {len(paragraphs)} paragraphs from database")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

    conn.close()
    return paragraphs


def load_paragraphs_from_file():
    """Load paragraphs from exported text file"""
    if not os.path.exists(PARAGRAPHS_FILE):
        print(f"Paragraphs file not found: {PARAGRAPHS_FILE}")
        return []

    paragraphs = []
    with open(PARAGRAPHS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and len(line) > 30:
                paragraphs.append(line)

    print(f"Loaded {len(paragraphs)} paragraphs from file")
    return paragraphs


def build_faiss_index(paragraphs, batch_size=100):
    """Build FAISS index from paragraphs"""
    if not paragraphs:
        print("No paragraphs to index!")
        return False

    print(f"\nBuilding FAISS index for {len(paragraphs)} paragraphs...")

    # Import here to avoid slow startup
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install sentence-transformers faiss-cpu")
        return False

    # Load model
    print("Loading embedding model...")
    if os.path.exists(MODEL_PATH):
        model = SentenceTransformer(MODEL_PATH)
        print(f"Using fine-tuned model: {MODEL_PATH}")
    else:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print("Using default multilingual model")

    # Create corpus database for search results
    print("Creating corpus database...")
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)
    cursor.execute("DELETE FROM corpus")

    for para in paragraphs:
        cursor.execute("INSERT INTO corpus (text) VALUES (?)", (para,))

    conn.commit()
    conn.close()
    print(f"Saved {len(paragraphs)} paragraphs to corpus.db")

    # Generate embeddings in batches
    print("Generating embeddings...")
    all_embeddings = []

    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_embeddings.append(batch_embeddings)

        progress = min(i + batch_size, len(paragraphs))
        print(f"  Processed {progress}/{len(paragraphs)} paragraphs")

    embeddings = np.vstack(all_embeddings)
    print(f"Generated embeddings shape: {embeddings.shape}")

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    index.add(embeddings)

    # Save index
    faiss.write_index(index, INDEX_PATH)
    print(f"Saved FAISS index to: {INDEX_PATH}")
    print(f"Index contains {index.ntotal} vectors of dimension {dimension}")

    return True


def main():
    print("=" * 60)
    print("FAISS INDEX BUILDER")
    print("=" * 60)

    # Try loading from database first, then file
    paragraphs = load_paragraphs_from_db()

    if not paragraphs:
        paragraphs = load_paragraphs_from_file()

    if not paragraphs:
        print("\nNo corpus data found!")
        print("Run the Wikipedia crawler first:")
        print("  python enhanced_wiki_crawler.py")
        return False

    # Limit to reasonable size for memory
    max_paragraphs = 5000
    if len(paragraphs) > max_paragraphs:
        print(f"\nLimiting to {max_paragraphs} paragraphs for memory efficiency")
        paragraphs = paragraphs[:max_paragraphs]

    success = build_faiss_index(paragraphs)

    if success:
        print("\n" + "=" * 60)
        print("FAISS INDEX BUILD COMPLETE")
        print("=" * 60)
    else:
        print("\nFAISS index build failed!")

    return success


if __name__ == "__main__":
    main()
