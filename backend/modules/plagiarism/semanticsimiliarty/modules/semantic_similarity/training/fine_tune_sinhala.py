from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import pandas as pd

# =========================
# CONFIG (EXPERIMENT 2)
# =========================
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DATA_PATH = "modules/semantic_similarity/training/sinhala_similarity_train_large.csv"
OUTPUT_DIR = "modules/semantic_similarity/training/fine_tuned_sinhala_model_large"

BATCH_SIZE = 16
EPOCHS = 2
LEARNING_RATE = 2e-5

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(DATA_PATH)

train_examples = []
for _, row in df.iterrows():
    train_examples.append(
        InputExample(
            texts=[str(row["sentence_1"]), str(row["sentence_2"])],
            label=float(row["label"])
        )
    )

train_dataloader = DataLoader(
    train_examples,
    shuffle=True,
    batch_size=BATCH_SIZE
)

# =========================
# LOAD MODEL
# =========================
model = SentenceTransformer(MODEL_NAME)

# =========================
# LOSS FUNCTION
# =========================
train_loss = losses.CosineSimilarityLoss(model)

# =========================
# TRAIN
# =========================
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=EPOCHS,
    warmup_steps=int(len(train_dataloader) * 0.1),
    optimizer_params={"lr": LEARNING_RATE},
    show_progress_bar=True
)

# =========================
# SAVE MODEL
# =========================
model.save(OUTPUT_DIR)

print("✅ Large dataset fine-tuning completed successfully")
