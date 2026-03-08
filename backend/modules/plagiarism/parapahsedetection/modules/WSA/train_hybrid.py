import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

# --- PATH SETUP ---
CURRENT_DIR = Path(__file__).resolve().parent
CSV_FILE_PATH = CURRENT_DIR / "training_data.csv"
MODEL_OUTPUT_PATH = CURRENT_DIR / "wsa_model.pkl"
VECTORIZER_PATH = CURRENT_DIR / "vectorizer.pkl"

def run_training():
    print("-" * 50)
    print("SINHALA PLAGIARISM TOOL: TRAINING ENGINE")
    print("-" * 50)
    
    if not CSV_FILE_PATH.exists():
        print(f"❌ ERROR: 'training_data.csv' not found at {CSV_FILE_PATH}")
        return

    try:
        # 1. Load Data
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
        print(f"✅ Data loaded: {len(df)} rows found.")

        # 2. Initialize TF-IDF Vectorizer
        # We use char_wb analyzer because it's better for Sinhala grammar/prefixes
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5))
        
        # 3. Fit and Transform the Sinhala text
        print("Training vectorizer on Sinhala text...")
        tfidf_matrix = vectorizer.fit_transform(df['text'].values.astype('U'))
        
        # 4. Save the models for use in main.py
        joblib.dump(vectorizer, VECTORIZER_PATH)
        joblib.dump(tfidf_matrix, CURRENT_DIR / "tfidf_matrix.pkl")
        # Saving the original dataframe as well to reference original texts
        joblib.dump(df, MODEL_OUTPUT_PATH)

        print(f"✅ SUCCESS: Model files saved in {CURRENT_DIR}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    run_training()