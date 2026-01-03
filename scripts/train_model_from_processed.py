import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score


# ==========================================
# 1. LOAD PROCESSED FEATURE DATASET
# ==========================================
df = pd.read_csv("data/processed/plagiarism_features.csv")

X = df[["semantic_sim", "paraphrase_sim", "style_sim"]]
y = df["label"]

print("Dataset size:", len(df))
print("Label distribution:")
print(y.value_counts())


# ==========================================
# 2. DEFINE REGRESSION MODEL
# ==========================================
pipeline = Pipeline([
    ("scaler", MinMaxScaler()),
    ("model", LogisticRegression(
        class_weight="balanced",
        solver="liblinear",
        random_state=42
    ))
])


# ==========================================
# 3. CROSS-VALIDATION (OPTIONAL BUT STRONG)
# ==========================================
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

auc_scores = []
f1_scores = []

for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    pipeline.fit(X_train, y_train)

    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)

    auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)

    auc_scores.append(auc)
    f1_scores.append(f1)

    print(f"Fold {fold}: ROC-AUC={auc:.3f}, F1={f1:.3f}")

print("\nMean ROC-AUC:", sum(auc_scores) / len(auc_scores))
print("Mean F1-score:", sum(f1_scores) / len(f1_scores))


# ==========================================
# 4. TRAIN FINAL MODEL ON ALL DATA
# ==========================================
pipeline.fit(X, y)

joblib.dump(
    pipeline,
    "backend/app/models/plagiarism/plagiarism_logreg_model.pkl"
)

print("\n✅ Final regression model trained and saved")
