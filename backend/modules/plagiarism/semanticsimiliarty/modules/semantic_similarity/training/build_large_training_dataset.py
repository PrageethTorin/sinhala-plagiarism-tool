import pandas as pd
import random

# =========================
# LOAD RAW DATA (NEW DATA ONLY)
# =========================
df_raw = pd.read_csv(
    "modules/semantic_similarity/training/sinhala_corpus_raw.csv"
)
df_para = pd.read_csv(
    "modules/semantic_similarity/training/sinhala_paraphrases.csv"
)

train_data = []

# =========================
# A. ADD PARAPHRASE PAIRS
# =========================
for _, row in df_para.iterrows():
    train_data.append({
        "sentence_1": row["sentence_1"],
        "sentence_2": row["sentence_2"],
        "label": float(row["label"])
    })

# =========================
# B. IDENTITY PAIRS (~15%)
# =========================
identity_samples = df_raw.sample(frac=0.15, random_state=42)

for _, row in identity_samples.iterrows():
    train_data.append({
        "sentence_1": row["sentence"],
        "sentence_2": row["sentence"],
        "label": 1.0
    })

# =========================
# C. CONTROLLED NEGATIVE SAMPLING (ACROSS TOPICS)
# =========================
topics = df_raw["topic"].unique()

for _ in range(len(df_raw) * 3):
    t1, t2 = random.sample(list(topics), 2)

    s1 = df_raw[df_raw.topic == t1].sample(1).sentence.values[0]
    s2 = df_raw[df_raw.topic == t2].sample(1).sentence.values[0]

    train_data.append({
        "sentence_1": s1,
        "sentence_2": s2,
        "label": 0.0
    })

# =========================
# SAVE FINAL TRAINING DATASET
# =========================
df_train = pd.DataFrame(train_data)
df_train.to_csv(
    "modules/semantic_similarity/training/sinhala_similarity_train_large.csv",
    index=False
)

print("✅ sinhala_similarity_train_large.csv created successfully")
print("Total training pairs:", len(df_train))
print("Label distribution:")
print(df_train["label"].value_counts())
