import pandas as pd
import numpy as np
import joblib
from tqdm import tqdm

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression

from app.models.plagiarism.similarity import (
    semantic_similarity,
    paraphrase_similarity,
    style_similarity
)

# --------------------------------------
# LOAD DATASET
# --------------------------------------
DATA_PATH = "backend/data/corpus_sources.csv"
df = pd.read_csv(DATA_PATH)

features = []
labels = []

print("Extracting similarity features...")

for _, row in tqdm(df.iterrows(), total=len(df)):
    source = str(row["source"])
    suspicious = str(row["suspicious"])
    label = int(row["label"])

    semantic = semantic_similarity(source, suspicious)
    paraphrase = paraphrase_similarity(source, suspicious)
    style = style_similarity(source, suspicious)

    features.append([semantic, paraphrase, style])
    labels.append(label)

X = np.array(features)
y = np.array(labels)

print("Feature shape:", X.shape)
print("Label distribution:", np.bincount(y))

# --------------------------------------
# TRAIN LOGISTIC REGRESSION
# --------------------------------------
pipeline = Pipeline([
    ("scaler", MinMaxScaler()),
    ("model", LogisticRegression(
        class_weight="balanced",
        solver="liblinear",
        random_state=42
    ))
])

pipeline.fit(X, y)

# --------------------------------------
# SAVE MODEL
# --------------------------------------
MODEL_PATH = "backend/app/models/plagiarism/plagiarism_logreg_model.pkl"
joblib.dump(pipeline, MODEL_PATH)

print("✅ Model trained and saved at:", MODEL_PATH)
