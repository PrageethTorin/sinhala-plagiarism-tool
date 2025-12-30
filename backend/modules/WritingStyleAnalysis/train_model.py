import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from feature_extractor import SinhalaStylometryExtractor

data = pd.read_csv('sinhala_dataset.csv')
extractor = SinhalaStylometryExtractor()

X = []
for text in data['text']:
    feats = extractor.analyze_style(text)
    X.append(list(feats.values()))

y = data['label']
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, 'plagiarism_model.pkl')
print("Model trained successfully with 4 features.")