# Sinhala Semantic Similarity - Model Comparison Report

Generated: 2025-12-31 14:50:45

Test samples: 260

## Results Summary

| Model | Precision | Recall | F1 | AUC | MSE | Pearson | Time(ms) |
|---|---|---|---|---|---|---|---|
| custom_only | 1.0000 | 0.1163 | 0.2083 | 0.9344 | 0.0824 | 0.6273 | 0.0 |
| multilingual_baseline | 0.3440 | 1.0000 | 0.5119 | 0.8792 | 0.3898 | 0.5657 | 1635.8 |
| finetuned_minilm | 1.0000 | 0.8837 | 0.9383 | 0.9997 | 0.0092 | 0.9671 | 164.7 |
| hybrid_approved | 1.0000 | 0.1279 | 0.2268 | 0.9344 | 0.0819 | 0.6293 | 0.8 |


## Model Details

### custom_only
- Description: Custom Algorithm: Jaccard(40%) + 2-gram(20%) + 3-gram(20%) + Word Order(20%)
- Optimal Threshold: 0.81
- Optimal F1: 1.0000

### multilingual_baseline
- Description: Pre-trained Multilingual MiniLM (no fine-tuning)
- Optimal Threshold: 0.60
- Optimal F1: 0.5190

### finetuned_minilm
- Description: Fine-tuned MiniLM on Sinhala data
- Optimal Threshold: 0.31
- Optimal F1: 0.9942

### hybrid_approved
- Description: Custom first, ML for difficult cases (0.4-0.7 range)
- Optimal Threshold: 0.81
- Optimal F1: 1.0000

