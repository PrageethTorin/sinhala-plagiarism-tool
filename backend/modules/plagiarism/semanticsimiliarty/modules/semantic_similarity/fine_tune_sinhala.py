"""
REAL fine-tuning using CUSTOM Sinhala STS dataset
Model: XLM-R
"""

import os
import sys
import csv


if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

print("Starting REAL Sinhala Fine-Tuning (XLM-R + Custom CSV)")


BASE_DIR = os.path.dirname(__file__)
EXPANDED_CSV = os.path.join(BASE_DIR, "training", "sinhala_similarity_train_expanded.csv")
LARGE_CSV = os.path.join(BASE_DIR, "training", "sinhala_similarity_train_large.csv")
CSV_PATH = EXPANDED_CSV if os.path.exists(EXPANDED_CSV) else LARGE_CSV


train_examples = []

with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        train_examples.append(
            InputExample(
                texts=[row["sentence_1"], row["sentence_2"]],
                label=float(row["label"])
            )
        )

print(f"Loaded {len(train_examples)} Sinhala sentence pairs")


MODEL_DIR = os.path.join(BASE_DIR, "sinhala_fine_tuned_model")

if os.path.exists(MODEL_DIR):
    print(f"Using existing fine-tuned model from: {MODEL_DIR}")
    model = SentenceTransformer(MODEL_DIR)
else:
    print("Downloading base XLM-R model (this may take a while)...")
    model = SentenceTransformer(
        "sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens"
    )


# Training setup

train_dataloader = DataLoader(
    train_examples,
    shuffle=True,
    batch_size=4   
)

train_loss = losses.CosineSimilarityLoss(model)

print("Fine-tuning model (1 epoch)...")

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,
    warmup_steps=50,
    show_progress_bar=True
)


# Save model (SAFE PATH)

model.save(MODEL_DIR)

print("Fine-tuning completed successfully!")
print(f"Model saved at: {MODEL_DIR}")
