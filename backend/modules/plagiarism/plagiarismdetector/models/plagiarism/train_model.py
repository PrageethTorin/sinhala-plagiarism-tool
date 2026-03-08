import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "..", "data", "score_dataset.csv")

print("Loading dataset from:", DATA_PATH)

df = pd.read_csv(DATA_PATH)

X = df[["semantic", "paraphrase", "style"]]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=2000)

print("Training model...")
model.fit(X_train, y_train)

pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, pred))

print("\nClassification Report:")
print(classification_report(y_test, pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, pred))

MODEL_PATH = os.path.join(BASE_DIR, "plagiarism_logreg_model.pkl")

joblib.dump(model, MODEL_PATH)

print("\nModel saved to:", MODEL_PATH)