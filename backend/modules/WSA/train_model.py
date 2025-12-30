# train_model.py
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from extractor import StyleExtractor
from preprocessor import SinhalaPreprocessor

def train():
    # 1. Load your dataset
    try:
        data = pd.read_csv('training_data.csv')
    except FileNotFoundError:
        print("❌ Error: training_data.csv not found!")
        return

    pre = SinhalaPreprocessor()
    ext = StyleExtractor()
    
    X = [] # Features
    y = [] # Labels

    print("📊 Extracting features from Sinhala text...")
    
    for index, row in data.iterrows():
        sentences = pre.split_into_sentences(row['text'])
        features = ext.get_all_features(row['text'], sentences)
        
        # Convert dictionary to a numerical list (Vector)
        vector = [
            features['avg_sentence_length'],
            features['vocabulary_richness'],
            features['punctuation_density']
        ]
        X.append(vector)
        y.append(row['label'])

    # 2. Train the Model
    print("🤖 Training the Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 3. Save the Model
    joblib.dump(model, 'wsa_model.pkl')
    print("✅ Model saved successfully as 'wsa_model.pkl'!")# train_model.py
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from extractor import StyleExtractor
from preprocessor import SinhalaPreprocessor

def train():
    # 1. Load the training data CSV
    # Ensure this file contains the Sinhala text samples and labels (0, 1, 2, 3)
    try:
        data = pd.read_csv('training_data.csv')
    except FileNotFoundError:
        print("❌ Error: training_data.csv not found in the current directory.")
        return

    # Initialize your research components
    pre = SinhalaPreprocessor()
    ext = StyleExtractor()
    
    X = [] # Feature vectors
    y = [] # Target labels

    print("📊 Extracting features (including Function Word Analysis)...")
    
    for index, row in data.iterrows():
        # Clean and split the text into sentences
        sentences = pre.split_into_sentences(row['text'])
        
        # Extract the 4 stylometric features
        features = ext.get_all_features(row['text'], sentences)
        
        # Build the vector: Model now expects 4 dimensions
        vector = [
            features['avg_sentence_length'],
            features['vocabulary_richness'],
            features['punctuation_density'],
            features['function_word_freq']  # The new standard-level feature
        ]
        
        X.append(vector)
        y.append(row['label'])

    # 2. Train the Machine Learning Model
    print(f"🤖 Training Random Forest Classifier on {len(X)} samples...")
    # Random Forest is ideal for stylometry as it handles non-linear feature relationships well
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 3. Save the Model as a binary file
    model_filename = 'wsa_model.pkl'
    joblib.dump(model, model_filename)
    
    print(f"✅ Model trained with 4 features and saved as '{model_filename}'!")

if __name__ == "__main__":
    train()

if __name__ == "__main__":
    train()