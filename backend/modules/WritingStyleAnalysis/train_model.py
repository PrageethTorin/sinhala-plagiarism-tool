import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from feature_extractor import SinhalaStylometryExtractor
import json

# 1. Load the Dataset
print("Loading dataset...")
try:
    df = pd.read_csv('sinhala_dataset.csv')
except FileNotFoundError:
    print("Error: Run 'create_dataset.py' first!")
    exit()

# 2. Extract Features
# We need to turn the Sinhala Text into Numbers (Vectors)
extractor = SinhalaStylometryExtractor()
features_list = []
labels_list = []

print("Extracting features from text...")

for index, row in df.iterrows():
    text = row['text']
    label = row['label']
    
    # Get the style dictionary
    style_data = extractor.analyze_style(text)
    
    if style_data:
        # Convert Dictionary values to a simple List of numbers
        # [Avg_Len, Vocab_Richness, Punctuation_Density]
        # Note: We skip 'function_word_freq' for now as it's complex JSON
        vector = [
            style_data['avg_sentence_length'],
            style_data['vocabulary_richness'],
            style_data['punctuation_density']
        ]
        features_list.append(vector)
        labels_list.append(label)

# 3. Prepare Data for Training
X = np.array(features_list) # The Input (Numbers)
y = np.array(labels_list)   # The Answer (0 or 1)

# Split: 80% for Training, 20% for Testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train the Model (Random Forest Algorithm)
print("Training the Random Forest Model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"🎉 Model Trained! Accuracy: {accuracy * 100:.2f}%")

# 6. Save the Model
joblib.dump(model, 'plagiarism_model.pkl')
print("✅ Model saved as 'plagiarism_model.pkl'")