"""
Model Evaluation Pipeline for Sinhala Semantic Similarity
Compares multiple models and generates comparison reports

Models to compare:
1. Custom Algorithm Only (Jaccard + N-gram + Word Order)
2. Baseline Multilingual Model (no fine-tuning)
3. Fine-tuned Multilingual Model
4. Hybrid Approach (Custom + Fine-tuned)
"""

import os
import sys
import csv
import json
import time
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import EvaluationMetrics, EvaluationResult, MultiThresholdEvaluator


@dataclass
class ModelConfig:
    """Configuration for a model to evaluate"""
    name: str
    model_type: str  # "custom", "pretrained", "finetuned", "hybrid"
    model_path: Optional[str] = None
    description: str = ""


class ModelEvaluator:
    """
    Evaluate and compare multiple semantic similarity models
    """

    MODELS_TO_COMPARE = [
        ModelConfig(
            name="custom_only",
            model_type="custom",
            description="Custom Algorithm: Jaccard(40%) + 2-gram(20%) + 3-gram(20%) + Word Order(20%)"
        ),
        ModelConfig(
            name="multilingual_baseline",
            model_type="pretrained",
            model_path="paraphrase-multilingual-MiniLM-L12-v2",
            description="Pre-trained Multilingual MiniLM (no fine-tuning)"
        ),
        ModelConfig(
            name="finetuned_minilm",
            model_type="finetuned",
            model_path="sinhala_fine_tuned_model",
            description="Fine-tuned MiniLM on Sinhala data"
        ),
        ModelConfig(
            name="hybrid_approved",
            model_type="hybrid",
            description="Custom first, ML for difficult cases (0.4-0.7 range)"
        )
    ]

    def __init__(self, test_data_path: str = None):
        """
        Initialize evaluator

        Args:
            test_data_path: Path to test dataset CSV
        """
        self.test_data_path = test_data_path
        self.test_pairs = []
        self.results = {}

        # Load custom algorithm
        try:
            from custom_algorithms import HybridSimilarityAlgorithm
            self.custom_algo = HybridSimilarityAlgorithm()
        except ImportError:
            print("Warning: custom_algorithms not found")
            self.custom_algo = None

        # Load fine-tuned model
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            self.pretrained_model = None
            self.finetuned_model = None
            self.cosine_similarity = cosine_similarity

        except ImportError:
            print("Warning: sentence_transformers not installed")
            self.pretrained_model = None
            self.finetuned_model = None

    def load_test_data(self, path: str = None) -> List[Dict]:
        """Load test dataset from CSV"""
        path = path or self.test_data_path

        if not path or not os.path.exists(path):
            print(f"Test data not found: {path}")
            return []

        pairs = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pairs.append({
                    "sentence_1": row["sentence_1"],
                    "sentence_2": row["sentence_2"],
                    "label": float(row["label"])
                })

        self.test_pairs = pairs
        print(f"Loaded {len(pairs)} test pairs")
        return pairs

    def _predict_custom(self, text1: str, text2: str) -> float:
        """Get prediction from custom algorithm"""
        if not self.custom_algo:
            return 0.5

        result = self.custom_algo.calculate_similarity(text1, text2)
        return result["similarity_score"]

    def _predict_pretrained(self, text1: str, text2: str) -> float:
        """Get prediction from pretrained model"""
        if not self.pretrained_model:
            try:
                from sentence_transformers import SentenceTransformer
                self.pretrained_model = SentenceTransformer(
                    "paraphrase-multilingual-MiniLM-L12-v2"
                )
            except Exception as e:
                print(f"Error loading pretrained model: {e}")
                return 0.5

        embeddings = self.pretrained_model.encode([text1, text2])
        similarity = self.cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)

    def _predict_finetuned(self, text1: str, text2: str) -> float:
        """Get prediction from fine-tuned model"""
        if not self.finetuned_model:
            try:
                from sentence_transformers import SentenceTransformer
                model_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "sinhala_fine_tuned_model"
                )
                if os.path.exists(model_path):
                    self.finetuned_model = SentenceTransformer(model_path)
                else:
                    print(f"Fine-tuned model not found at {model_path}")
                    return self._predict_pretrained(text1, text2)
            except Exception as e:
                print(f"Error loading fine-tuned model: {e}")
                return 0.5

        embeddings = self.finetuned_model.encode([text1, text2])
        similarity = self.cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)

    def _predict_hybrid(self, text1: str, text2: str) -> float:
        """
        Get prediction from hybrid approach
        Custom first, ML only for difficult cases (0.4-0.7)
        """
        custom_score = self._predict_custom(text1, text2)

        # Easy cases: use custom only
        if custom_score < 0.4 or custom_score > 0.7:
            return custom_score

        # Difficult cases: combine with embedding
        embedding_score = self._predict_finetuned(text1, text2)
        final_score = (custom_score + embedding_score) / 2

        return final_score

    def predict_batch(self, model_type: str) -> List[float]:
        """Get predictions for all test pairs"""
        predictions = []

        predict_fn = {
            "custom": self._predict_custom,
            "pretrained": self._predict_pretrained,
            "finetuned": self._predict_finetuned,
            "hybrid": self._predict_hybrid
        }.get(model_type, self._predict_custom)

        for pair in self.test_pairs:
            score = predict_fn(pair["sentence_1"], pair["sentence_2"])
            predictions.append(score)

        return predictions

    def evaluate_model(self, model_config: ModelConfig,
                        threshold: float = 0.5) -> Dict:
        """Evaluate a single model"""
        print(f"\nEvaluating: {model_config.name}")
        print(f"  Type: {model_config.model_type}")

        start_time = time.time()

        # Get predictions
        predictions = self.predict_batch(model_config.model_type)
        labels = [p["label"] for p in self.test_pairs]

        inference_time = time.time() - start_time

        # Calculate metrics
        evaluator = EvaluationMetrics(threshold=threshold)
        result = evaluator.evaluate_all(
            np.array(predictions),
            np.array(labels)
        )

        # Find optimal threshold
        multi_eval = MultiThresholdEvaluator()
        optimal_thresh, best_f1 = multi_eval.find_optimal_threshold(
            np.array(predictions),
            np.array(labels)
        )

        return {
            "model_name": model_config.name,
            "model_type": model_config.model_type,
            "description": model_config.description,
            "results": result.to_dict(),
            "optimal_threshold": optimal_thresh,
            "optimal_f1": best_f1,
            "inference_time_seconds": round(inference_time, 2),
            "avg_time_per_sample_ms": round(inference_time * 1000 / len(self.test_pairs), 2)
        }

    def evaluate_all_models(self, threshold: float = 0.5) -> List[Dict]:
        """Evaluate all configured models"""
        if not self.test_pairs:
            print("No test data loaded. Call load_test_data() first.")
            return []

        all_results = []

        for model_config in self.MODELS_TO_COMPARE:
            try:
                result = self.evaluate_model(model_config, threshold)
                all_results.append(result)
                self.results[model_config.name] = result
            except Exception as e:
                print(f"Error evaluating {model_config.name}: {e}")

        return all_results

    def generate_comparison_table(self) -> str:
        """Generate markdown comparison table"""
        if not self.results:
            return "No results to display"

        headers = ["Model", "Precision", "Recall", "F1", "AUC", "MSE", "Pearson", "Time(ms)"]
        rows = []

        for name, data in self.results.items():
            r = data["results"]
            rows.append([
                name,
                f"{r['precision']:.4f}",
                f"{r['recall']:.4f}",
                f"{r['f1_score']:.4f}",
                f"{r['roc_auc']:.4f}",
                f"{r['mse']:.4f}",
                f"{r['pearson_r']:.4f}",
                f"{data['avg_time_per_sample_ms']:.1f}"
            ])

        # Create markdown table
        table = "| " + " | ".join(headers) + " |\n"
        table += "|" + "|".join(["---"] * len(headers)) + "|\n"
        for row in rows:
            table += "| " + " | ".join(row) + " |\n"

        return table

    def save_results(self, output_dir: str = None) -> str:
        """Save evaluation results to files"""
        output_dir = output_dir or os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_path = os.path.join(output_dir, f"model_comparison_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_samples": len(self.test_pairs),
                "models": list(self.results.values())
            }, f, indent=2)

        # Save markdown report
        md_path = os.path.join(output_dir, f"model_comparison_{timestamp}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Sinhala Semantic Similarity - Model Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Test samples: {len(self.test_pairs)}\n\n")
            f.write("## Results Summary\n\n")
            f.write(self.generate_comparison_table())
            f.write("\n\n## Model Details\n\n")
            for name, data in self.results.items():
                f.write(f"### {name}\n")
                f.write(f"- Description: {data['description']}\n")
                f.write(f"- Optimal Threshold: {data['optimal_threshold']:.2f}\n")
                f.write(f"- Optimal F1: {data['optimal_f1']:.4f}\n\n")

        # Save CSV
        csv_path = os.path.join(output_dir, f"model_comparison_{timestamp}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Model", "Precision", "Recall", "F1", "AUC", "MSE",
                            "Pearson", "Optimal_Threshold", "Time_ms"])
            for name, data in self.results.items():
                r = data["results"]
                writer.writerow([
                    name, r["precision"], r["recall"], r["f1_score"],
                    r["roc_auc"], r["mse"], r["pearson_r"],
                    data["optimal_threshold"], data["avg_time_per_sample_ms"]
                ])

        print(f"\nResults saved:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        print(f"  CSV: {csv_path}")

        return json_path


def run_evaluation(test_data_path: str):
    """Run complete evaluation pipeline"""
    print("=" * 60)
    print("SINHALA SEMANTIC SIMILARITY - MODEL EVALUATION")
    print("=" * 60)

    evaluator = ModelEvaluator(test_data_path)
    evaluator.load_test_data()

    if not evaluator.test_pairs:
        print("No test data available. Please provide test data.")
        return

    # Run evaluation
    results = evaluator.evaluate_all_models(threshold=0.5)

    # Print comparison
    print("\n" + "=" * 60)
    print("COMPARISON TABLE")
    print("=" * 60)
    print(evaluator.generate_comparison_table())

    # Save results
    evaluator.save_results()

    return results


if __name__ == "__main__":
    # Example usage
    test_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "training",
        "sinhala_similarity_train_large.csv"
    )

    if os.path.exists(test_path):
        run_evaluation(test_path)
    else:
        print(f"Test data not found at: {test_path}")
        print("Please provide a valid test data path")
