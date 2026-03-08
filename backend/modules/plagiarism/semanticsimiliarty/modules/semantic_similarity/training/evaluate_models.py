from sentence_transformers import SentenceTransformer, util
import pandas as pd

# =========================
# PATHS (RELATIVE & GIT-SAFE)
# =========================
DATA_PATH = "modules/semantic_similarity/training/sinhala_similarity.csv"


BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SMALL_FT_MODEL = "modules/semantic_similarity/training/fine_tuned_sinhala_model"
LARGE_FT_MODEL = "modules/semantic_similarity/training/fine_tuned_sinhala_model_large"

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(DATA_PATH)

# Expected columns:
# sentence_1, sentence_2, label, type

# =========================
# LOAD MODELS
# =========================
print("🔹 Loading base model...")
base_model = SentenceTransformer(BASE_MODEL)

print("🔹 Loading small fine-tuned model...")
small_ft_model = SentenceTransformer(SMALL_FT_MODEL)

print("🔹 Loading large fine-tuned model...")
large_ft_model = SentenceTransformer(LARGE_FT_MODEL)

# =========================
# SIMILARITY FUNCTION
# =========================
def compute_similarity(model, s1, s2):
    emb1 = model.encode(s1, convert_to_tensor=True)
    emb2 = model.encode(s2, convert_to_tensor=True)
    return util.cos_sim(emb1, emb2).item()

# =========================
# COMPUTE SIMILARITIES
# =========================
base_scores = []
small_ft_scores = []
large_ft_scores = []

for _, row in df.iterrows():
    s1 = str(row["sentence_1"])
    s2 = str(row["sentence_2"])

    base_scores.append(compute_similarity(base_model, s1, s2))
    small_ft_scores.append(compute_similarity(small_ft_model, s1, s2))
    large_ft_scores.append(compute_similarity(large_ft_model, s1, s2))

df["base_similarity"] = base_scores
df["small_ft_similarity"] = small_ft_scores
df["large_ft_similarity"] = large_ft_scores

# =========================
# GROUP ANALYSIS
# =========================
results = df.groupby("type")[[
    "base_similarity",
    "small_ft_similarity",
    "large_ft_similarity"
]].mean()

print("\n📊 AVERAGE SIMILARITY SCORES BY TYPE")
print(results)

# =========================
# SAVE RESULTS
# =========================
results.to_csv(
    "modules/semantic_similarity/training/evaluation_results_phase3.csv"
)

print("\n✅ Phase 3 evaluation completed successfully")
